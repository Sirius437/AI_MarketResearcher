"""Market data management and aggregation for cryptocurrency trading."""

import asyncio
import logging
import fcntl
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os

from .binance_client import BinanceClient
from .interactive_brokers_client import InteractiveBrokersClient
from .polygon_client import PolygonClient
from .finnhub_client import FinnhubClient
from .alpha_vantage_client import AlphaVantageClient
from .yahoo_client import YahooFinanceClient
from .indicators import TechnicalIndicators
from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class MarketDataManager:
    """Manage market data fetching, caching, and processing."""
    
    def __init__(self, binance_client: BinanceClient, config: MarketResearcherConfig):
        """Initialize market data manager."""
        self.config = config
        self.binance_client = binance_client
        self.indicators = TechnicalIndicators()
        self.cache_dir = Path(config.data_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Interactive Brokers client as primary source for non-crypto data
        try:
            self.ib_client = InteractiveBrokersClient()
            logger.info("Interactive Brokers client initialized as primary data source")
        except Exception as e:
            logger.warning(f"Interactive Brokers client failed to initialize: {e}")
            self.ib_client = None
        
        # Initialize Finnhub client as secondary source for non-crypto data (best free tier)
        try:
            finnhub_key = getattr(config, 'finnhub_api_key', None)
            if finnhub_key:
                self.finnhub_client = FinnhubClient(finnhub_key)
                logger.info("Finnhub client initialized as secondary data source")
            else:
                self.finnhub_client = None
                logger.warning("Finnhub API key not found in config")
        except Exception as e:
            logger.warning(f"Finnhub client failed to initialize: {e}")
            self.finnhub_client = None
        
        # Initialize fallback stock data sources: Polygon -> Alpha Vantage -> Yahoo
        try:
            polygon_key = getattr(config, 'polygon_api_key', None)
            if polygon_key:
                self.polygon_client = PolygonClient(polygon_key)
                logger.info("Polygon client initialized for stock data")
            else:
                self.polygon_client = None
                logger.warning("Polygon API key not found in config")
        except Exception as e:
            logger.warning(f"Polygon client failed to initialize: {e}")
            self.polygon_client = None
            
        try:
            alpha_key = getattr(config, 'alpha_vantage_api_key', 'demo')
            self.alpha_vantage_client = AlphaVantageClient(alpha_key)
            logger.info("Alpha Vantage client initialized for stock data")
        except Exception as e:
            logger.warning(f"Alpha Vantage client failed to initialize: {e}")
            self.alpha_vantage_client = None
        
        try:
            self.yahoo_client = YahooFinanceClient()
            logger.info("Yahoo Finance client initialized for stock data")
        except Exception as e:
            logger.warning(f"Yahoo Finance client failed to initialize: {e}")
            self.yahoo_client = None
        
        # Initialize Binance client for crypto data
        try:
            self.binance_client = BinanceClient(self.config)
            self.binance_client._initialize_client()  # Properly initialize the client
            logger.info("Binance client created and initialized")
        except Exception as e:
            logger.error(f"Failed to create Binance client: {e}")
            self.binance_client = None
        
        # Data storage
        self._price_cache = {}
        self._indicator_cache = {}
        self._last_update = {}
    
    def _is_forex_symbol(self, symbol: str) -> bool:
        """Detect if a symbol is a forex pair."""
        symbol = symbol.upper()
        
        # Common forex pairs (6-character format like EURUSD, GBPUSD)
        forex_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
            'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD', 'EURCAD', 'EURNZD',
            'GBPJPY', 'GBPCHF', 'GBPAUD', 'GBPCAD', 'GBPNZD',
            'AUDJPY', 'AUDCHF', 'AUDCAD', 'AUDNZD',
            'CADJPY', 'CADCHF', 'NZDJPY', 'NZDCHF', 'NZDCAD',
            'CHFJPY'
        ]
        
        # Check if symbol matches known forex pairs
        if symbol in forex_pairs:
            return True
            
        # Check if symbol follows forex pattern (6 chars, all letters)
        if len(symbol) == 6 and symbol.isalpha():
            # Check if it's composed of valid currency codes
            base = symbol[:3]
            quote = symbol[3:]
            valid_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD', 'SEK', 'NOK', 'DKK', 'PLN', 'CZK', 'HUF', 'TRY', 'ZAR', 'MXN', 'SGD', 'HKD', 'CNY', 'INR', 'KRW', 'BRL', 'RUB']
            return base in valid_currencies and quote in valid_currencies
            
        return False
    
    async def get_market_overview(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get market overview for specified symbols."""
        if symbols is None:
            symbols = self.config.default_symbols
        
        try:
            overview = {}
            for symbol in symbols:
                # Determine symbol type: crypto, forex, or stock
                is_crypto = any(crypto_suffix in symbol.upper() for crypto_suffix in ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD'])
                is_forex = self._is_forex_symbol(symbol)
                
                if self.binance_client and self.binance_client.client and is_crypto:
                    try:
                        ticker = self.binance_client.get_24hr_ticker(symbol)
                        if ticker and ticker.get('price', 0) > 0:
                            overview[symbol] = {
                                'price': ticker['price'],
                                'change_24h': ticker['priceChangePercent'],
                                'volume': ticker['volume'],
                                'high_24h': ticker['high'],
                                'low_24h': ticker['low']
                            }
                            logger.info(f"Binance successfully fetched data for {symbol}")
                        else:
                            logger.warning(f"Binance returned invalid data for {symbol}")
                            overview[symbol] = {'price': 0, 'change_24h': 0, 'volume': 0, 'high_24h': 0, 'low_24h': 0}
                    except Exception as e:
                        logger.error(f"Error fetching crypto data for {symbol}: {e}")
                        overview[symbol] = {'price': 0, 'change_24h': 0, 'volume': 0, 'high_24h': 0, 'low_24h': 0}
                elif is_crypto:
                    # Crypto symbol but no working Binance client - try public API
                    try:
                        # Import the public crypto API
                        from data.public_crypto_api import PublicCryptoAPI
                        
                        # Create a public crypto API client
                        public_api = PublicCryptoAPI()
                        
                        # Get ticker data from public API
                        ticker_data = public_api.get_ticker_data(symbol)
                        
                        if ticker_data and ticker_data.get('price', 0) > 0:
                            logger.info(f"Using public API for crypto data: {symbol}")
                            overview[symbol] = {
                                'price': float(ticker_data.get('price', 0)),
                                'change_24h': float(ticker_data.get('priceChange', 0)),
                                'change_percent_24h': float(ticker_data.get('priceChangePercent', 0)),
                                'volume': float(ticker_data.get('volume', 0)),
                                'high_24h': float(ticker_data.get('price', 0)) * 1.01,  # Estimate
                                'low_24h': float(ticker_data.get('price', 0)) * 0.99,   # Estimate
                            }
                        else:
                            logger.warning(f"Public API returned invalid data for {symbol}")
                            overview[symbol] = {'price': 0, 'change_24h': 0, 'volume': 0, 'high_24h': 0, 'low_24h': 0}
                    except Exception as e:
                        logger.error(f"Error fetching public crypto data for {symbol}: {e}")
                        overview[symbol] = {'price': 0, 'change_24h': 0, 'volume': 0, 'high_24h': 0, 'low_24h': 0}
                elif is_forex:
                    # Handle forex symbols - prioritize IB for forex data
                    forex_data_found = False
                    
                    # Try Interactive Brokers first for forex (best forex data source)
                    if self.ib_client and not forex_data_found:
                        try:
                            # Connect if not already connected
                            if not self.ib_client.is_connected():
                                await self.ib_client.connect()
                            
                            if self.ib_client.is_connected():
                                forex_data = await self.ib_client.get_quote(symbol, "forex")
                                if (forex_data and isinstance(forex_data, dict) and not forex_data.get('error') and 
                                    forex_data.get('price') is not None and forex_data.get('price', 0) > 0):
                                    overview[symbol] = {
                                        'price': forex_data.get('price', 0),
                                        'change_24h': forex_data.get('change_percent', 0),
                                        'volume': forex_data.get('volume', 0),
                                        'high_24h': forex_data.get('high', 0),
                                        'low_24h': forex_data.get('low', 0)
                                    }
                                    forex_data_found = True
                                    logger.info(f"Interactive Brokers successfully fetched forex data for {symbol}")
                        except Exception as e:
                            logger.warning(f"Interactive Brokers failed for forex {symbol}: {e}")
                    
                    # Try Finnhub as fallback for forex
                    if self.finnhub_client and not forex_data_found:
                        try:
                            forex_data = self.finnhub_client.get_quote(symbol)
                            if forex_data and isinstance(forex_data, dict) and not forex_data.get('error') and forex_data.get('current_price', 0) > 0:
                                overview[symbol] = {
                                    'price': forex_data.get('current_price', 0),
                                    'change_24h': forex_data.get('percent_change', 0),
                                    'volume': forex_data.get('volume', 0),
                                    'high_24h': forex_data.get('high', 0),
                                    'low_24h': forex_data.get('low', 0)
                                }
                                forex_data_found = True
                                logger.info(f"Finnhub successfully fetched forex data for {symbol}")
                        except Exception as e:
                            logger.warning(f"Finnhub failed for forex {symbol}: {e}")
                    
                    # If all forex sources fail, provide default data
                    if not forex_data_found:
                        logger.warning(f"All forex data sources failed for {symbol}")
                        overview[symbol] = {'price': 0, 'change_24h': 0, 'volume': 0, 'high_24h': 0, 'low_24h': 0}
                else:
                    # Try stock data sources in priority order: IB -> Finnhub -> Polygon -> Alpha Vantage -> Yahoo
                    stock_data_found = False
                    
                    # 1. Try Interactive Brokers first (highest priority - real-time data)
                    if self.ib_client and not stock_data_found:
                        try:
                            # Connect if not already connected
                            if not self.ib_client.is_connected():
                                await self.ib_client.connect()
                            
                            if self.ib_client.is_connected():
                                stock_data = await self.ib_client.get_quote(symbol, "stock")
                                if (stock_data and isinstance(stock_data, dict) and not stock_data.get('error') and 
                                    stock_data.get('price') is not None and stock_data.get('price', 0) > 0):
                                    
                                    overview[symbol] = {
                                        'price': stock_data.get('price', 0),
                                        'change_24h': stock_data.get('change_percent', 0),
                                        'volume': stock_data.get('volume', 0),
                                        'high_24h': stock_data.get('high', stock_data.get('price', 0)),
                                        'low_24h': stock_data.get('low', stock_data.get('price', 0))
                                    }
                                    stock_data_found = True
                                    logger.info(f"Interactive Brokers successfully fetched data for {symbol}")
                                # Disconnect to prevent client ID conflicts
                                await self.ib_client.disconnect()
                        except Exception as e:
                            logger.warning(f"Interactive Brokers failed for {symbol}: {e}")
                    
                    # 2. Try Finnhub as fallback (good free tier)
                    if self.finnhub_client and not stock_data_found:
                        try:
                            stock_data = await self.finnhub_client.get_quote(symbol)
                            if stock_data and isinstance(stock_data, dict) and not stock_data.get('error') and stock_data.get('current_price', 0) > 0:
                                currency = self._get_stock_currency(symbol)
                                overview[symbol] = {
                                    'price': stock_data.get('current_price', 0),
                                    'change_24h': stock_data.get('percent_change', 0),
                                    'volume': stock_data.get('volume', 0),
                                    'high_24h': stock_data.get('high', 0),
                                    'low_24h': stock_data.get('low', 0),
                                    'currency': currency
                                }
                                stock_data_found = True
                                logger.info(f"Finnhub successfully fetched data for {symbol}")
                        except Exception as e:
                            logger.warning(f"Finnhub failed for {symbol}: {e}")
                    
                    # 3. Try Polygon as third priority
                    if self.polygon_client and not stock_data_found:
                        try:
                            stock_data = await self.polygon_client.get_quote(symbol)
                            if stock_data and isinstance(stock_data, dict) and not stock_data.get('error') and stock_data.get('price', 0) > 0:
                                currency = self._get_stock_currency(symbol)
                                overview[symbol] = {
                                    'price': stock_data.get('price', 0),
                                    'change_24h': stock_data.get('change_percent', 0),
                                    'volume': stock_data.get('volume', 0),
                                    'high_24h': stock_data.get('high', 0),
                                    'low_24h': stock_data.get('low', 0),
                                    'currency': currency
                                }
                                stock_data_found = True
                                logger.info(f"Polygon successfully fetched data for {symbol}")
                        except Exception as e:
                            logger.warning(f"Polygon failed for {symbol}: {e}")
                    
                    # 4. Try Alpha Vantage as fourth priority
                    if self.alpha_vantage_client and not stock_data_found:
                        try:
                            stock_data = await self.alpha_vantage_client.get_quote(symbol)
                            if stock_data and isinstance(stock_data, dict) and stock_data.get('price', 0) > 0:
                                currency = self._get_stock_currency(symbol)
                                overview[symbol] = {
                                    'price': stock_data.get('price', 0),
                                    'change_24h': stock_data.get('change_percent', 0),
                                    'volume': stock_data.get('volume', 0),
                                    'high_24h': stock_data.get('high', 0),
                                    'low_24h': stock_data.get('low', 0),
                                    'currency': currency
                                }
                                stock_data_found = True
                                logger.info(f"Alpha Vantage successfully fetched data for {symbol}")
                        except Exception as e:
                            logger.warning(f"Alpha Vantage failed for {symbol}: {e}")
                    
                    # 5. Try Yahoo Finance as final fallback
                    if self.yahoo_client and not stock_data_found:
                        try:
                            # For Malaysian stocks, use .KL suffix for Yahoo Finance
                            from .exchanges.klse_numeric_to_symbol_map import is_numeric_klse_code, get_yahoo_symbol_from_numeric_code
                            yahoo_symbol = get_yahoo_symbol_from_numeric_code(symbol) if is_numeric_klse_code(symbol) else symbol
                            
                            stock_data = await self.yahoo_client.get_stock_info(yahoo_symbol)
                            if stock_data and isinstance(stock_data, dict) and stock_data.get('regularMarketPrice', 0) > 0:
                                # Get currency information for the stock
                                currency = self._get_stock_currency(symbol)
                                
                                overview[symbol] = {
                                    'price': stock_data.get('regularMarketPrice', 0),
                                    'change_24h': stock_data.get('regularMarketChangePercent', 0),
                                    'volume': stock_data.get('regularMarketVolume', 0),
                                    'high_24h': stock_data.get('regularMarketDayHigh', 0),
                                    'low_24h': stock_data.get('regularMarketDayLow', 0),
                                    'currency': currency
                                }
                                stock_data_found = True
                                logger.info(f"Yahoo Finance successfully fetched data for {symbol} using {yahoo_symbol}")
                        except Exception as e:
                            logger.warning(f"Yahoo Finance failed for {symbol}: {e}")
                    
                    # If all stock sources fail, provide default data
                    if not stock_data_found:
                        logger.warning(f"All stock data sources failed for {symbol}")
                        overview[symbol] = {'price': 0, 'change_24h': 0, 'volume': 0, 'high_24h': 0, 'low_24h': 0}
                        
            return overview
        except Exception as e:
            logger.error(f"Error fetching market overview: {e}")
            return {}
        finally:
            # Close any open async sessions to prevent resource warnings
            try:
                if hasattr(self, 'alpha_vantage_client') and self.alpha_vantage_client and hasattr(self.alpha_vantage_client, 'session'):
                    await self.alpha_vantage_client.session.close()
                if hasattr(self, 'yahoo_client') and self.yahoo_client and hasattr(self.yahoo_client, 'session'):
                    await self.yahoo_client.session.close()
                if hasattr(self, 'polygon_client') and self.polygon_client and hasattr(self.polygon_client, 'session'):
                    await self.polygon_client.session.close()
            except Exception as e:
                logger.debug(f"Error closing sessions: {e}")
    
    async def get_symbol_data(
        self, 
        symbol: str, 
        timeframe: str = "1h", 
        limit: int = 100,
        include_indicators: bool = True
    ) -> pd.DataFrame:
        """Get comprehensive data for a single symbol."""
        try:
            # Check cache first
            cache_key = f"{symbol}_{timeframe}_{limit}"
            if self._is_cache_valid(cache_key):
                logger.info(f"Using cached data for {symbol}")
                return self._get_cached_data(cache_key)
            
            # Determine symbol type: crypto, forex, or stock
            is_crypto = any(crypto_suffix in symbol.upper() for crypto_suffix in ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD'])
            is_forex = self._is_forex_symbol(symbol)
            
            if is_crypto and self.binance_client and self.binance_client.client:
                # Use Binance for crypto historical data
                end_time = datetime.now()
                # Use the limit parameter to determine how many days to fetch
                days_to_fetch = limit if timeframe == '1d' else max(limit // 24, 30)  # Convert hours to days if needed
                start_time = end_time - timedelta(days=days_to_fetch)
                
                try:
                    df = self.binance_client.get_historical_klines(
                        symbol=symbol,
                        interval=timeframe,
                        start_time=start_time,
                        end_time=end_time,
                        limit=limit
                    )
                    
                    if df is not None and not df.empty:
                        logger.info(f"Binance successfully fetched data for {symbol}")
                        
                        if include_indicators:
                            df = self.indicators.calculate_all_indicators(df)
                        
                        # Cache the data
                        self._cache_data(cache_key, df)
                        self._last_update[cache_key] = datetime.now()
                        return df
                    else:
                        logger.warning(f"Binance returned empty data for {symbol}")
                        return pd.DataFrame()
                        
                except Exception as e:
                    logger.error(f"Binance failed for {symbol}: {e}")
                    return pd.DataFrame()
            elif is_forex:
                # Handle forex symbols - prioritize IB for forex historical data
                if self.ib_client:
                    try:
                        # Map timeframe for IB
                        ib_timeframe, ib_duration = self._map_timeframe_for_ib(timeframe, limit)
                        
                        # Connect if not already connected
                        if not self.ib_client.is_connected():
                            await self.ib_client.connect()
                        
                        if self.ib_client.is_connected():
                            df = await self.ib_client.get_historical_data(
                                symbol=symbol,
                                duration=ib_duration,
                                bar_size=ib_timeframe,
                                asset_type="forex"
                            )
                            
                            if not df.empty:
                                logger.info(f"Interactive Brokers successfully fetched forex historical data for {symbol}")
                                
                                if include_indicators:
                                    df = self.indicators.calculate_all_indicators(df)
                                
                                # Cache the data
                                self._cache_data(cache_key, df)
                                self._last_update[cache_key] = datetime.now()
                                return df
                        
                        # Disconnect after use to prevent client ID conflicts
                        if self.ib_client.is_connected():
                            await self.ib_client.disconnect()
                            
                    except Exception as e:
                        logger.error(f"Interactive Brokers failed for forex {symbol}: {e}")
                
                # Fallback to other sources for forex if IB fails
                logger.warning(f"No forex historical data available for {symbol}")
                return pd.DataFrame()
            else:
                # Use Finnhub first for stock data with fallback chain
                data_sources = [
                    ('Finnhub', self.finnhub_client),
                    ('Interactive Brokers', self.ib_client),
                    ('Polygon', self.polygon_client),
                    ('Alpha Vantage', self.alpha_vantage_client),
                    ('Yahoo Finance', self.yahoo_client)
                ]
                
                for source_name, client in data_sources:
                    if client is None:
                        continue
                        
                    try:
                        if source_name == 'Finnhub':
                            # Finnhub doesn't provide historical candles in free tier
                            df = self.finnhub_client.get_historical_data(symbol, timeframe)
                            if isinstance(df, dict) and df.get('error'):
                                # Skip to next source if historical data not available
                                continue
                            elif not df.empty:
                                logger.info(f"Finnhub successfully fetched historical data for {symbol}")
                                break
                        elif source_name == 'Interactive Brokers':
                            # Map timeframe for IB
                            ib_timeframe, ib_duration = self._map_timeframe_for_ib(timeframe, limit)
                            
                            # Connect if not already connected
                            if not self.ib_client.is_connected():
                                await self.ib_client.connect()
                            
                            if self.ib_client.is_connected():
                                df = await self.ib_client.get_historical_data(
                                    symbol=symbol,
                                    duration=ib_duration,
                                    bar_size=ib_timeframe,
                                    asset_type="stock"
                                )
                                
                                if not df.empty:
                                    logger.info(f"Interactive Brokers successfully fetched historical data for {symbol}")
                                    break
                            # Disconnect after use to prevent client ID conflicts
                            if self.ib_client.is_connected():
                                await self.ib_client.disconnect()
                        elif source_name == 'Polygon':
                            # Calculate date range for Polygon API
                            end_date = datetime.now().strftime('%Y-%m-%d')
                            start_date = (datetime.now() - timedelta(days=self.config.historical_days)).strftime('%Y-%m-%d')
                            
                            # Map timeframe to Polygon timespan
                            timespan_map = {
                                '1m': 'minute',
                                '5m': 'minute', 
                                '15m': 'minute',
                                '30m': 'minute',
                                '1h': 'hour',
                                '4h': 'hour',
                                '1d': 'day',
                                '1w': 'week',
                                '1M': 'month'
                            }
                            
                            timespan = timespan_map.get(timeframe, 'day')
                            multiplier = 1
                            if timeframe == '5m':
                                multiplier = 5
                            elif timeframe == '15m':
                                multiplier = 15
                            elif timeframe == '30m':
                                multiplier = 30
                            elif timeframe == '4h':
                                multiplier = 4
                            
                            df = await self.polygon_client.get_aggregates(
                                symbol=symbol,
                                multiplier=multiplier,
                                timespan=timespan,
                                start_date=start_date,
                                end_date=end_date,
                                limit=limit
                            )
                            if not df.empty:
                                logger.info(f"Polygon successfully fetched historical data for {symbol}")
                                break
                        # Finnhub is now handled first in the loop
                        elif source_name == 'Alpha Vantage':
                            df = await self.alpha_vantage_client.get_historical_data(symbol, timeframe, limit)
                            if not df.empty:
                                logger.info(f"Alpha Vantage successfully fetched historical data for {symbol}")
                                break
                        elif source_name == 'Yahoo Finance':
                            # For Malaysian stocks, use .KL suffix for Yahoo Finance
                            from .exchanges.klse_numeric_to_symbol_map import is_numeric_klse_code, get_yahoo_symbol_from_numeric_code
                            yahoo_symbol = get_yahoo_symbol_from_numeric_code(symbol) if is_numeric_klse_code(symbol) else symbol
                            
                            df = await self.yahoo_client.get_historical_data(yahoo_symbol, timeframe, limit)
                            if not df.empty:
                                logger.info(f"Yahoo Finance successfully fetched historical data for {symbol} using {yahoo_symbol}")
                                break
                    except Exception as e:
                        logger.warning(f"{source_name} failed for {symbol}: {e}")
                
                if 'df' not in locals():
                    logger.warning(f"All data sources failed for {symbol}")
                    return pd.DataFrame()
                
                if include_indicators:
                    df = self.indicators.calculate_all_indicators(df)
                
                # Cache the data if we have any
                if 'df' in locals() and df is not None and not df.empty:
                    self._cache_data(cache_key, df)
                    self._last_update[cache_key] = datetime.now()
                    return df
                
                # If no data found from any source
                logger.warning(f"No historical data available for {symbol}")
                return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _map_timeframe_for_ib(self, timeframe: str, limit: int) -> tuple:
        """Map timeframe and limit to IB API format."""
        # Map timeframe to IB bar size
        timeframe_mapping = {
            '1m': '1 min',
            '5m': '5 mins',
            '15m': '15 mins',
            '30m': '30 mins',
            '1h': '1 hour',
            '4h': '4 hours',
            '1d': '1 day',
            '1w': '1 week',
            '1M': '1 month'
        }
        
        ib_timeframe = timeframe_mapping.get(timeframe, '1 hour')
        
        # Calculate duration based on timeframe and limit
        if timeframe in ['1m', '5m']:
            duration = f"{limit * 5} D"  # Days for minute data
        elif timeframe in ['15m', '30m', '1h']:
            duration = f"{limit // 24 + 1} D"  # Days for hourly data
        elif timeframe == '4h':
            duration = f"{limit // 6 + 1} D"  # Days for 4-hour data
        elif timeframe == '1d':
            duration = f"{limit} D"  # Days
        elif timeframe == '1w':
            duration = f"{limit} W"  # Weeks
        elif timeframe == '1M':
            duration = f"{limit} M"  # Months
        else:
            duration = "30 D"  # Default
            
        return ib_timeframe, duration
    
    async def get_multi_timeframe_data(
        self, 
        symbol: str, 
        timeframes: Optional[List[str]] = None
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple timeframes."""
        if timeframes is None:
            timeframes = self.config.analysis_timeframes
        
        result = {}
        for tf in timeframes:
            try:
                df = await self.get_symbol_data(symbol, tf, include_indicators=True)
                if not df.empty:
                    result[tf] = df
            except Exception as e:
                logger.error(f"Error fetching {tf} data for {symbol}: {e}")
        
        return result
    
    def get_market_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """Get market sentiment indicators."""
        try:
            # Determine if symbol is crypto or stock
            is_crypto = any(crypto_suffix in symbol.upper() for crypto_suffix in ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD'])
            
            if not is_crypto:
                # For stocks, return basic sentiment data
                logger.info(f"Using basic sentiment data for stock symbol: {symbol}")
                return {'sentiment_score': 50, 'buy_pressure': 50, 'sell_pressure': 50}
            
            # Get order book for sentiment analysis (crypto only)
            if not self.binance_client or not self.binance_client.client:
                logger.warning(f"Binance client not available for sentiment: {symbol}")
                return {'sentiment_score': 0, 'buy_pressure': 0, 'sell_pressure': 0}
                
            order_book = self.binance_client.get_order_book(symbol, limit=100)
            
            # Calculate bid/ask ratio
            total_bid_volume = sum(qty for _, qty in order_book['bids'][:10])
            total_ask_volume = sum(qty for _, qty in order_book['asks'][:10])
            bid_ask_ratio = total_bid_volume / total_ask_volume if total_ask_volume > 0 else 0
            
            # Get recent trades for volume analysis
            recent_trades = self.binance_client.get_recent_trades(symbol, limit=100)
            
            # Calculate buy/sell pressure
            buy_volume = sum(trade['qty'] for trade in recent_trades if not trade['is_buyer_maker'])
            sell_volume = sum(trade['qty'] for trade in recent_trades if trade['is_buyer_maker'])
            buy_sell_ratio = buy_volume / sell_volume if sell_volume > 0 else 0
            
            return {
                'bid_ask_ratio': bid_ask_ratio,
                'buy_sell_ratio': buy_sell_ratio,
                'total_bid_volume': total_bid_volume,
                'total_ask_volume': total_ask_volume,
                'recent_buy_volume': buy_volume,
                'recent_sell_volume': sell_volume,
                'order_book_depth': len(order_book['bids']) + len(order_book['asks'])
            }
            
        except Exception as e:
            logger.error(f"Error fetching sentiment data for {symbol}: {e}")
            return {}
    
    async def calculate_correlation_matrix(
        self, 
        symbols: Optional[List[str]] = None, 
        timeframe: str = "1h",
        period: int = 30
    ) -> pd.DataFrame:
        """Calculate correlation matrix between symbols."""
        if symbols is None:
            symbols = self.config.default_symbols
        
        try:
            price_data = {}
            
            for symbol in symbols:
                df = await self.get_symbol_data(symbol, timeframe, limit=period * 24)
                if not df.empty:
                    price_data[symbol] = df['close'].pct_change().dropna()
            
            if price_data:
                correlation_df = pd.DataFrame(price_data)
                return correlation_df.corr()
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    
    async def get_volatility_metrics(self, symbol: str, timeframe: str = "1h") -> Dict[str, float]:
        """Calculate volatility metrics for a symbol."""
        try:
            df = await self.get_symbol_data(symbol, timeframe, limit=100)
            if df.empty:
                return {}
            
            returns = df['close'].pct_change().dropna()
            
            # Calculate various volatility metrics
            volatility_1d = returns.tail(24).std() * np.sqrt(24)  # 24 hours
            volatility_7d = returns.tail(168).std() * np.sqrt(168)  # 7 days
            volatility_30d = returns.std() * np.sqrt(len(returns))  # Full period
            
            # Calculate VaR (Value at Risk) at 95% confidence
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)
            
            # Calculate maximum drawdown
            cumulative_returns = (1 + returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            return {
                'volatility_1d': volatility_1d,
                'volatility_7d': volatility_7d,
                'volatility_30d': volatility_30d,
                'var_95': var_95,
                'var_99': var_99,
                'max_drawdown': max_drawdown,
                'current_price': df['close'].iloc[-1],
                'price_change_24h': returns.tail(24).sum()
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility metrics for {symbol}: {e}")
            return {}
    
    def get_liquidity_score(self, symbol: str) -> float:
        """Calculate liquidity score based on order book depth and spread."""
        try:
            # Determine if symbol is crypto or stock
            is_crypto = any(crypto_suffix in symbol.upper() for crypto_suffix in ['USDT', 'BTC', 'ETH', 'BNB', 'BUSD'])
            
            if not is_crypto:
                # For stocks, return basic liquidity score
                logger.info(f"Using basic liquidity score for stock symbol: {symbol}")
                return 75.0  # Assume reasonable liquidity for major stocks
            
            if not self.binance_client or not self.binance_client.client:
                logger.warning(f"Binance client not available for liquidity: {symbol}")
                return 0.0
                
            order_book = self.binance_client.get_order_book(symbol, limit=100)
            
            if not order_book['bids'] or not order_book['asks']:
                return 0.0
            
            # Calculate spread
            best_bid = order_book['bids'][0][0]
            best_ask = order_book['asks'][0][0]
            spread = (best_ask - best_bid) / best_ask
            
            # Calculate depth (total volume in top 10 levels)
            bid_depth = sum(qty for _, qty in order_book['bids'][:10])
            ask_depth = sum(qty for _, qty in order_book['asks'][:10])
            total_depth = bid_depth + ask_depth
            
            # Liquidity score (inverse of spread, weighted by depth)
            if spread > 0:
                liquidity_score = (1 / spread) * np.log(1 + total_depth)
            else:
                liquidity_score = np.log(1 + total_depth)
            
            # Normalize to 0-100 scale
            return min(100, max(0, liquidity_score / 10))
            
        except Exception as e:
            logger.error(f"Error calculating liquidity score for {symbol}: {e}")
            return 0.0
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._last_update:
            return False
        
        time_diff = datetime.now() - self._last_update[cache_key]
        return time_diff.total_seconds() < self.config.price_update_interval
    
    def _get_cached_data(self, cache_key: str) -> pd.DataFrame:
        """Retrieve data from cache."""
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with self._safe_file_read(cache_file, 'rb') as f:
                    return pd.read_pickle(f)
            except Exception as e:
                logger.error(f"Error reading cache file {cache_file}: {e}")
        
        return pd.DataFrame()
    
    def _safe_file_read(self, file_path: Path, mode: str = 'rb'):
        """Context manager for safe file reading with locking."""
        class SafeFileReader:
            def __init__(self, file_path, mode):
                self.file_path = file_path
                self.mode = mode
                self.file = None
                
            def __enter__(self):
                self.file = open(self.file_path, self.mode)
                fcntl.flock(self.file.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                return self.file
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.file:
                    fcntl.flock(self.file.fileno(), fcntl.LOCK_UN)  # Unlock
                    self.file.close()
                    
        return SafeFileReader(file_path, mode)
    
    def _safe_file_write(self, file_path: Path, mode: str = 'wb'):
        """Context manager for safe file writing with locking."""
        class SafeFileWriter:
            def __init__(self, file_path, mode):
                self.file_path = file_path
                self.mode = mode
                self.file = None
                self.temp_file = None
                
            def __enter__(self):
                # Create temporary file in same directory
                dir_path = self.file_path.parent
                self.temp_file = tempfile.NamedTemporaryFile(
                    mode=self.mode, 
                    dir=dir_path, 
                    delete=False,
                    prefix=self.file_path.name + '.tmp'
                )
                fcntl.flock(self.temp_file.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                return self.temp_file
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.temp_file:
                    fcntl.flock(self.temp_file.fileno(), fcntl.LOCK_UN)  # Unlock
                    self.temp_file.close()
                    
                    if exc_type is None:  # No exception occurred
                        # Atomically replace original file
                        os.replace(self.temp_file.name, self.file_path)
                    else:
                        # Remove temp file on error
                        try:
                            os.unlink(self.temp_file.name)
                        except:
                            pass
                            
        return SafeFileWriter(file_path, mode)
    
    def _cache_data(self, cache_key: str, data: pd.DataFrame):
        """Cache data to disk."""
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            with self._safe_file_write(cache_file, 'wb') as f:
                data.to_pickle(f.name)
        except Exception as e:
            logger.error(f"Error caching data for {cache_key}: {e}")
    
    def clear_cache(self):
        """Clear all cached data."""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
            self._price_cache.clear()
            self._indicator_cache.clear()
            self._last_update.clear()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_market_summary(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get comprehensive market summary."""
        if symbols is None:
            symbols = self.config.default_symbols
        
        try:
            summary = {
                'timestamp': datetime.now().isoformat(),
                'symbols': {},
                'market_metrics': {}
            }
            
            # Get individual symbol data
            for symbol in symbols:
                try:
                    if not self.binance_client:
                        logger.warning(f"Binance client not available for market stats: {symbol}")
                        continue
                        
                    ticker = self.binance_client.get_24hr_ticker(symbol)
                    volatility = self.get_volatility_metrics(symbol)
                    liquidity = self.get_liquidity_score(symbol)
                    
                    summary['symbols'][symbol] = {
                        'price': ticker['price'],
                        'change_24h': ticker['price_change_percent'],
                        'volume': ticker['volume'],
                        'volatility_24h': volatility.get('volatility_1d', 0),
                        'liquidity_score': liquidity
                    }
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
            
            # Calculate market-wide metrics
            if summary['symbols']:
                prices = [data['change_24h'] for data in summary['symbols'].values()]
                summary['market_metrics'] = {
                    'avg_change_24h': np.mean(prices),
                    'market_volatility': np.std(prices),
                    'positive_symbols': sum(1 for p in prices if p > 0),
                    'total_symbols': len(prices)
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return {}
    
    def _get_stock_currency(self, symbol: str) -> str:
        """Get currency for a stock symbol by looking up in stocks database."""
        try:
            from data.stocks_database import StocksDatabase
            stocks_db = StocksDatabase()
            stock_info = stocks_db.get_stock_by_symbol(symbol)
            if stock_info and stock_info.currency:
                return stock_info.currency
        except Exception:
            pass
        
        # Default to USD if not found
        return 'USD'
    
    async def get_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive financial metrics with Finnhub → Yahoo fallback prioritization."""
        try:
            # 1. Try Finnhub first for financial data (reliable and fast)
            if self.finnhub_client:
                try:
                    financials = self.finnhub_client.get_basic_financials(symbol)
                    if financials and not financials.get('error'):
                        logger.info(f"Finnhub successfully fetched financial metrics for {symbol}")
                        return {
                            'pe_ratio': financials.get('pe_ratio'),
                            'pb_ratio': financials.get('price_to_book'),
                            'roa': financials.get('roa'), 
                            'roe': financials.get('roe'),
                            'revenue_growth': financials.get('revenue_growth'),
                            'eps': financials.get('eps'),
                            'debt_to_equity': financials.get('debt_to_equity'),
                            'current_ratio': financials.get('current_ratio'),
                            'gross_margin': financials.get('gross_margin'),
                            'operating_margin': financials.get('operating_margin'),
                            'net_margin': financials.get('net_margin'),
                            'beta': financials.get('beta'),
                            'source': 'Finnhub'
                        }
                except Exception as e:
                    logger.warning(f"Finnhub financial data failed for {symbol}: {e}")
            
            # 2. Try Yahoo Finance as fallback
            if self.yahoo_client:
                try:
                    financials = await self.yahoo_client.get_financials(symbol)
                    if financials and not financials.get('error'):
                        logger.info(f"Yahoo Finance successfully fetched financial metrics for {symbol}")
                        return {
                            'pe_ratio': financials.get('pe_ratio'),
                            'pb_ratio': financials.get('pb_ratio'),
                            'roa': financials.get('roa'),
                            'roe': financials.get('roe'), 
                            'revenue_growth': financials.get('revenue_growth'),
                            'eps': financials.get('eps'),
                            'debt_to_equity': financials.get('debt_to_equity'),
                            'current_ratio': financials.get('current_ratio'),
                            'gross_margin': financials.get('gross_margin'),
                            'operating_margin': financials.get('operating_margin'),
                            'net_margin': financials.get('net_margin'),
                            'beta': financials.get('beta'),
                            'source': 'Yahoo Finance'
                        }
                except Exception as e:
                    logger.warning(f"Yahoo Finance financial data failed for {symbol}: {e}")
            
            # Return empty metrics if all sources fail
            logger.warning(f"All financial data sources failed for {symbol}")
            return {
                'pe_ratio': 'N/A',
                'pb_ratio': 'N/A', 
                'roa': 'N/A',
                'roe': 'N/A',
                'revenue_growth': 'N/A',
                'eps': 'N/A',
                'debt_to_equity': 'N/A',
                'current_ratio': 'N/A',
                'gross_margin': 'N/A',
                'operating_margin': 'N/A',
                'net_margin': 'N/A',
                'beta': 'N/A',
                'source': 'None - All sources failed'
            }
            
        except Exception as e:
            logger.error(f"Error fetching financial metrics for {symbol}: {e}")
            return {'error': str(e)}
