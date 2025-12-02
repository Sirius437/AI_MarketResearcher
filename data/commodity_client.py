"""
Commodity futures data client using multiple APIs.
Supports Alpha Vantage and Polygon.io for commodity futures data.
"""

import os
import time
import logging
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
import os

logger = logging.getLogger(__name__)


class CommodityClient:
    """Client for commodity futures data using multiple APIs with intelligent fallback chain."""
    
    def __init__(self, alpha_vantage_key: str = None, polygon_key: str = None, 
                 nasdaq_key: str = None, fred_key: str = None):
        """Initialize commodity client with API keys."""
        self.alpha_vantage_key = alpha_vantage_key or os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.polygon_key = polygon_key or os.getenv('POLYGON_API_KEY')
        self.nasdaq_key = nasdaq_key or os.getenv('NASDAQ_API_KEY')
        self.fred_key = fred_key or os.getenv('FRED_API_KEY')
        self.session = None
        
        # Initialize clients
        self.polygon_client = None
        self.nasdaq_client = None
        self.fred_client = None
        self.yahoo_client = None
        
        # Initialize data sources with fallback chain
        # Primary: Interactive Brokers -> Secondary: Yahoo Finance -> Tertiary: FRED -> Final: Others
        self.data_sources = []
        self.ib_client = None
        
        # Rate limiting
        self.rate_limit = 5  # requests per minute
        self.rate_window = 60  # seconds
        self.request_times = []
        
    async def initialize(self):
        """Initialize HTTP session and data clients."""
        self.session = aiohttp.ClientSession()
        
        # Initialize Interactive Brokers client first (primary source for latest data)
        try:
            from .interactive_brokers_client import InteractiveBrokersClient
            self.ib_client = InteractiveBrokersClient()
            self.data_sources.append('interactive_brokers')
            logger.info("Interactive Brokers client initialized as primary source")
        except Exception as e:
            logger.warning(f"Failed to initialize Interactive Brokers client: {e}")
            self.ib_client = None
        
        # Polygon is now secondary source
        # NASDAQ moved to backup due to access restrictions
        polygon_api_key = os.getenv('POLYGON_API_KEY')
        if polygon_api_key:
            try:
                from .polygon_client import PolygonClient
                self.polygon_client = PolygonClient(polygon_api_key)
                logger.info("Polygon client initialized as primary source")
            except Exception as e:
                logger.warning(f"Failed to initialize Polygon client: {e}")
                self.polygon_client = None
        else:
            logger.warning("Polygon API key not found")
            self.polygon_client = None
        
        nasdaq_api_key = os.getenv('NASDAQ_API_KEY')
        if nasdaq_api_key:
            try:
                from .nasdaq_client import NASDAQClient
                self.nasdaq_client = NASDAQClient(nasdaq_api_key)
                logger.info("NASDAQ client initialized as backup source")
            except Exception as e:
                logger.warning(f"Failed to initialize NASDAQ client: {e}")
                self.nasdaq_client = None
        else:
            logger.warning("NASDAQ API key not found")
            self.nasdaq_client = None
        
        # Initialize FRED client if key available
        fred_api_key = os.getenv('FRED_API_KEY')
        if fred_api_key:
            try:
                from .fred_client import FREDClient
                # Create minimal config object for FREDClient
                class FREDConfig:
                    def __init__(self, api_key):
                        self.fred_api_key = api_key
                
                fred_config = FREDConfig(fred_api_key)
                self.fred_client = FREDClient(fred_config)
                self.data_sources.append('fred')
                logger.info("FRED client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize FRED client: {e}")
                self.fred_client = None
        else:
            logger.warning("FRED API key not found")
            self.fred_client = None
        
        # Initialize Yahoo Finance client
        try:
            from .yahoo_client import YahooFinanceClient
            self.yahoo_client = YahooFinanceClient()
            self.data_sources.append('yahoo')
            logger.info("Yahoo Finance client initialized successfully")
        except ImportError:
            logger.warning("Yahoo Finance client not available")
            self.yahoo_client = None
        
        # Set primary data source order - Interactive Brokers first for latest data!
        self.primary_sources = ['interactive_brokers', 'yahoo', 'fred', 'polygon', 'alpha_vantage']
        logger.info(f"Initialized commodity client with sources: {self.data_sources}")
        
    async def close(self):
        """Close HTTP session and data clients."""
        if self.session:
            await self.session.close()
        if self.polygon_client:
            await self.polygon_client.close()
        if self.nasdaq_client:
            await self.nasdaq_client.close()
        if self.fred_client:
            await self.fred_client.close()
        if self.ib_client:
            await self.ib_client.close()
        if self.yahoo_client:
            await self.yahoo_client.close()
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        now = time.time()
        
        # Remove requests older than rate window
        self.request_times = [t for t in self.request_times if now - t < self.rate_window]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.rate_limit:
            sleep_time = self.rate_window - (now - self.request_times[0]) + 1
            logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
            await asyncio.sleep(sleep_time)
            
        # Record this request
        self.request_times.append(now)
    
    async def _make_alpha_vantage_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to Alpha Vantage API."""
        await self._rate_limit_check()
        
        if not self.session:
            await self.initialize()
        
        url = "https://www.alphavantage.co/query"
        params['apikey'] = self.alpha_vantage_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for API error messages
                    if "Error Message" in data:
                        return {"error": data["Error Message"]}
                    if "Note" in data:
                        return {"error": f"API limit: {data['Note']}"}
                    
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"Alpha Vantage API request failed: {response.status} - {error_text}")
                    return {"error": f"API request failed: {response.status}"}
                    
        except Exception as e:
            logger.error(f"Alpha Vantage request error: {e}")
            return {"error": str(e)}
    
    async def _make_polygon_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make request to Polygon.io API."""
        if not self.polygon_key:
            return {"error": "Polygon API key not available"}
            
        await self._rate_limit_check()
        
        if not self.session:
            await self.initialize()
        
        url = f"https://api.polygon.io{endpoint}"
        params = params or {}
        params['apikey'] = self.polygon_key
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    # Rate limited, wait and retry
                    logger.warning("Rate limited by Polygon API, waiting 60 seconds")
                    await asyncio.sleep(60)
                    return await self._make_polygon_request(endpoint, params)
                else:
                    error_text = await response.text()
                    logger.error(f"Polygon API request failed: {response.status} - {error_text}")
                    return {"error": f"API request failed: {response.status}"}
                    
        except Exception as e:
            logger.error(f"Polygon request error: {e}")
            return {"error": str(e)}
    
    def _map_symbol_to_nasdaq(self, symbol: str) -> str:
        """Map futures symbols to NASDAQ commodity codes."""
        nasdaq_mapping = {
            'CL=F': 'CRUDE_OIL_WTI',  # Crude Oil WTI
            'BZ=F': 'CRUDE_OIL_BRENT',  # Brent Crude Oil
            'NG=F': 'NATURAL_GAS',  # Natural Gas
            'HG=F': 'COPPER',  # Copper
            'GC=F': 'GOLD',  # Gold
            'SI=F': 'SILVER',  # Silver
            'ZW=F': 'WHEAT',  # Wheat
            'ZC=F': 'CORN',  # Corn
            'ZS=F': 'SOYBEANS',  # Soybeans
            'CT=F': 'COTTON',  # Cotton
            'SB=F': 'SUGAR',  # Sugar
            'KC=F': 'COFFEE',  # Coffee
        }
        return nasdaq_mapping.get(symbol, None)
    
    def _map_symbol_to_fred(self, symbol: str) -> str:
        """Map futures symbols to FRED commodity series IDs."""
        fred_mapping = {
            'CL=F': 'DCOILWTICO',  # Crude Oil WTI
            'BZ=F': 'DCOILBRENTEU',  # Brent Crude Oil
            'NG=F': 'DHHNGSP',  # Natural Gas
            'HG=F': 'PCOPPUSDM',  # Copper
            'GC=F': 'NASDAQQGLDI',  # Gold (corrected)
            'SI=F': 'NASDAQQSLVO',  # Silver (corrected)
            'CC=F': 'PCOCOUSDM',  # Cocoa (corrected)
            # Note: The following commodities are not available on FRED
            # and will fall back to Alpha Vantage or Yahoo Finance:
            # ZW=F (Wheat), ZC=F (Corn), ZS=F (Soybeans),
            # CT=F (Cotton), SB=F (Sugar), KC=F (Coffee), LBS=F (Lumber)
        }
        return fred_mapping.get(symbol, None)

    def _map_symbol_to_ib(self, symbol: str) -> tuple:
        """Map commodity symbol to IB symbol and exchange using verified working contracts."""
        # Use only verified working IB commodity contracts (continuous futures preferred)
        ib_mapping = {
            # Yahoo Finance symbols to IB continuous futures
            'CL=F': ('CL', 'NYMEX'),        # Oil continuous future - VERIFIED WORKING
            'GC=F': ('GC', 'COMEX'),        # Gold continuous future - VERIFIED WORKING  
            'NG=F': ('NG', 'NYMEX'),        # Natural Gas continuous future - VERIFIED WORKING
            'SI=F': ('SI', 'COMEX'),        # Silver continuous future
            'PL=F': ('PL', 'NYMEX'),        # Platinum continuous future
            'HG=F': ('HG', 'COMEX'),        # Copper continuous future
            # Generic symbols
            'GOLD': ('GC', 'COMEX'),        
            'SILVER': ('SI', 'COMEX'),      
            'PLATINUM': ('PL', 'NYMEX'),    
            'CRUDE_OIL': ('CL', 'NYMEX'),   
            'NATURAL_GAS': ('NG', 'NYMEX'), 
            'COPPER': ('HG', 'COMEX'),      
        }
        return ib_mapping.get(symbol, (symbol, 'SMART'))

    def _map_symbol_to_alpha_vantage(self, symbol: str) -> str:
        """Map futures symbols to Alpha Vantage commodity symbols."""
        symbol_mapping = {
            'CL=F': 'WTI',
            'BZ=F': 'BRENT', 
            'NG=F': 'NATURAL_GAS',
            'HG=F': 'COPPER',
            'ALI=F': 'ALUMINUM',
            'ZW=F': 'WHEAT',
            'ZC=F': 'CORN',
            'CT=F': 'COTTON',
            'SB=F': 'SUGAR',
            'KC=F': 'COFFEE',
        }
        return symbol_mapping.get(symbol, symbol)

    async def get_commodity_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Get real-time commodity quote with multi-source fallback
        
        Args:
            symbol: Commodity symbol (e.g., 'CL=F', 'GC=F')
            
        Returns:
            Dict containing quote data or error
        """
        logger.info(f"Getting commodity quote for {symbol}")
        
        # 1. Try Interactive Brokers first (primary source for latest data)
        ib_symbol, ib_exchange = self._map_symbol_to_ib(symbol)
        if ib_symbol and self.ib_client:
            try:
                logger.info(f"Trying Interactive Brokers for {symbol} -> {ib_symbol} on {ib_exchange}")
                
                # Connect to IB if not already connected
                if not self.ib_client.is_connected():
                    connected = await self.ib_client.connect()
                    if not connected:
                        logger.warning("Failed to connect to IB Gateway/TWS")
                        raise Exception("IB connection failed")
                
                quote_data = await self.ib_client.get_quote(ib_symbol, asset_type="commodity", exchange=ib_exchange)
                if quote_data and 'error' not in quote_data:
                    return {
                        'symbol': symbol,
                        'price': quote_data.get('price'),
                        'change': quote_data.get('change'),
                        'change_percent': quote_data.get('change_percent'),
                        'volume': quote_data.get('volume'),
                        'timestamp': quote_data.get('timestamp'),
                        'source': 'Interactive Brokers'
                    }
            except Exception as e:
                logger.warning(f"Interactive Brokers quote failed for {symbol}: {e}")
        
        # 2. Try Yahoo Finance (secondary source for latest data)
        if self.yahoo_client:
            try:
                logger.info(f"Trying Yahoo Finance for {symbol}")
                quote_data = await self.yahoo_client.get_quote(symbol)
                if quote_data and 'error' not in quote_data:
                    return {
                        'symbol': symbol,
                        'price': quote_data.get('price'),
                        'change': quote_data.get('change'),
                        'change_percent': quote_data.get('change_percent'),
                        'volume': quote_data.get('volume'),
                        'timestamp': quote_data.get('timestamp'),
                        'source': 'Yahoo Finance'
                    }
            except Exception as e:
                logger.warning(f"Yahoo Finance quote failed for {symbol}: {e}")
        
        # 3. Try FRED for economic commodity data (tertiary source)
        fred_series = self._map_symbol_to_fred(symbol)
        if fred_series and self.fred_client:
            try:
                logger.info(f"Trying FRED for {symbol} -> {fred_series}")
                fred_symbol = self._get_fred_symbol(symbol)
                
                # Get latest data point with recent date range
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                data = await self.fred_client.get_series(fred_symbol, start_date=start_date, end_date=end_date, limit=10)
                if data and 'observations' in data:
                    obs = data['observations']
                    if obs and len(obs) > 0:
                        latest = obs[-1]
                        if latest.get('value', '.') != '.':
                            return {
                                'symbol': symbol,
                                'price': float(latest['value']),
                                'change': None,
                                'change_percent': None,
                                'volume': None,
                                'timestamp': latest.get('date'),
                                'source': 'FRED'
                            }
            except Exception as e:
                logger.warning(f"FRED quote failed for {symbol}: {e}")
        
        # 4. Try Polygon (fallback source)
        if self.polygon_client:
            try:
                logger.info(f"Trying Polygon for {symbol}")
                quote_data = await self.polygon_client.get_quote(symbol)
                if quote_data and 'error' not in quote_data:
                    return {
                        'symbol': symbol,
                        'price': quote_data.get('price'),
                        'change': None,  # Polygon last trade doesn't provide change
                        'change_percent': None,
                        'volume': quote_data.get('size'),
                        'timestamp': quote_data.get('timestamp'),
                        'source': 'Polygon'
                    }
            except Exception as e:
                logger.warning(f"Polygon quote failed for {symbol}: {e}")
        
        # 2. Try Alpha Vantage for mapped commodities
        av_symbol = self._map_symbol_to_alpha_vantage(symbol)
        if av_symbol != symbol:  # Symbol was mapped, use Alpha Vantage
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": av_symbol
            }
            
            logger.info(f"Trying Alpha Vantage for {symbol} -> {av_symbol}")
            result = await self._make_alpha_vantage_request(params)
            
            if 'error' not in result and 'Global Quote' in result:
                logger.info(f"Alpha Vantage data retrieved successfully for {symbol}")
                return result
        
        # 3. Try FRED for economic commodity data
        fred_series = self._map_symbol_to_fred(symbol)
        # Try FRED fallback
        if self.fred_client:
            try:
                logger.info(f"Trying FRED for {symbol} -> {self._get_fred_symbol(symbol)}")
                fred_symbol = self._get_fred_symbol(symbol)
                
                # Get latest data point with recent date range
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                data = await self.fred_client.get_series(fred_symbol, start_date=start_date, end_date=end_date, limit=10)
                if data and 'observations' in data:
                    obs = data['observations']
                    if obs and len(obs) > 0:
                        latest = obs[-1]
                        return {
                            'symbol': symbol,
                            'price': float(latest['value']) if latest['value'] != '.' else None,
                            'change': None,  # FRED doesn't provide change data
                            'change_percent': None,
                            'volume': None,
                            'date': latest['date'],
                            'source': 'FRED'
                        }
                        
            except Exception as e:
                logger.error(f"FRED fallback failed for {symbol}: {e}")
        
        # 4. Final fallback to Yahoo Finance
        if self.yahoo_client:
            try:
                logger.info(f"Trying Yahoo Finance for {symbol}")
                quote_data = await self.yahoo_client.get_quote(symbol)
                if quote_data and 'error' not in quote_data:
                    return {
                        'symbol': symbol,
                        'price': quote_data.get('regularMarketPrice'),
                        'change': quote_data.get('regularMarketChange'),
                        'change_percent': quote_data.get('regularMarketChangePercent'),
                        'volume': quote_data.get('regularMarketVolume'),
                        'timestamp': quote_data.get('regularMarketTime'),
                        'source': 'Yahoo Finance'
                    }
            except Exception as e:
                logger.error(f"Yahoo Finance fallback failed for {symbol}: {e}")
        
        # All sources failed
        logger.error(f"All data sources failed for {symbol}")
        return {'error': f'No data available for {symbol}', 'symbol': symbol}
        
    def _get_fred_symbol(self, symbol: str) -> str:
        """Map commodity symbols to FRED series IDs."""
        fred_mappings = {
            'CL=F': 'DCOILWTICO',  # WTI Crude Oil (Daily)
            'BZ=F': 'DCOILBRENTEU',  # Brent Crude Oil (Daily)  
            'NG=F': 'DHHNGSP',  # Natural Gas (Daily)
            'GC=F': 'NASDAQQGLDI',  # Gold (corrected)
            'SI=F': 'NASDAQQSLVO',  # Silver (corrected)
            'HG=F': 'PCOPPUSDM',  # Copper (Monthly)
            'ZC=F': 'PMAIZMTUSDM',  # Corn (Monthly)
            'ZS=F': 'PSOYBUSDM',  # Soybeans (Monthly)
            'ZW=F': 'PWHEAMTUSDM',  # Wheat (Monthly)
            'KC=F': 'PCOFFOTMUSDM',  # Coffee (Monthly)
            'SB=F': 'PSUGAISAUSDM',  # Sugar (Monthly)
            'CC=F': 'PCOCOUSDM',  # Cocoa (corrected)
        }
        return fred_mappings.get(symbol, symbol)
    
    async def get_commodity_daily(self, symbol: str, outputsize: str = "compact") -> Dict[str, Any]:
        """Get daily commodity data using intelligent fallback chain."""
        logger.info(f"Getting daily commodity data for {symbol}")
        
        # 1. Try NASDAQ first
        nasdaq_symbol = self._map_symbol_to_nasdaq(symbol)
        if nasdaq_symbol and self.nasdaq_client:
            logger.info(f"Trying NASDAQ for daily data {symbol} -> {nasdaq_symbol}")
            try:
                days = 365 if outputsize == "full" else 100
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                df = await self.nasdaq_client.get_commodity_prices(
                    nasdaq_symbol,
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                
                if not df.empty:
                    # Convert to Alpha Vantage format
                    time_series = {}
                    for date, row in df.iterrows():
                        date_str = date.strftime('%Y-%m-%d')
                        price = row.iloc[0]
                        time_series[date_str] = {
                            '1. open': str(price),
                            '2. high': str(price),
                            '3. low': str(price),
                            '4. close': str(price),
                            '5. volume': '0'
                        }
                    
                    daily_data = {
                        'Meta Data': {
                            '1. Information': f'Daily Prices for {symbol}',
                            '2. Symbol': symbol,
                            '3. Last Refreshed': max(time_series.keys()),
                            '4. Output Size': outputsize,
                            '5. Time Zone': 'US/Eastern'
                        },
                        'Time Series (Daily)': time_series
                    }
                    logger.info(f"NASDAQ daily data retrieved successfully for {symbol}")
                    return daily_data
            except Exception as e:
                logger.error(f"NASDAQ daily data failed for {symbol}: {e}")
        
        # 2. Try Alpha Vantage for mapped commodities
        av_symbol = self._map_symbol_to_alpha_vantage(symbol)
        if av_symbol != symbol:
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": av_symbol,
                "outputsize": outputsize
            }
            
            logger.info(f"Trying Alpha Vantage for daily data {symbol} -> {av_symbol}")
            result = await self._make_alpha_vantage_request(params)
            
            if 'error' not in result and 'Time Series (Daily)' in result:
                logger.info(f"Alpha Vantage daily data retrieved successfully for {symbol}")
                return result
        
        # 3. Try FRED for economic commodity data
        fred_series = self._map_symbol_to_fred(symbol)
        if fred_series and self.fred_client:
            logger.info(f"Trying FRED for daily data {symbol} -> {fred_series}")
            try:
                limit = 365 if outputsize == "full" else 100
                df = await self.fred_client.get_series(fred_series, limit=limit)
                
                if not df.empty:
                    # Convert FRED data to Alpha Vantage daily format
                    time_series = {}
                    for date, row in df.iterrows():
                        date_str = date.strftime('%Y-%m-%d')
                        price = row.iloc[0]
                        time_series[date_str] = {
                            '1. open': str(price),
                            '2. high': str(price),
                            '3. low': str(price),
                            '4. close': str(price),
                            '5. volume': '0'
                        }
                    
                    daily_data = {
                        'Meta Data': {
                            '1. Information': f'Daily Prices for {symbol}',
                            '2. Symbol': symbol,
                            '3. Last Refreshed': max(time_series.keys()),
                            '4. Output Size': outputsize,
                            '5. Time Zone': 'US/Eastern'
                        },
                        'Time Series (Daily)': time_series
                    }
                    logger.info(f"FRED daily data retrieved successfully for {symbol}")
                    return daily_data
            except Exception as e:
                logger.error(f"No daily data available for {symbol}")
        return pd.DataFrame()
    
    async def get_commodity_intraday_data(self, symbol: str, interval: str = "60min") -> Dict[str, Any]:
        """Get intraday commodity data using intelligent fallback chain."""
        logger.info(f"Getting intraday commodity data for {symbol}")
        
        # 1. Try Polygon first (primary source)
        if self.polygon_client:
            try:
                logger.info(f"Trying Polygon for intraday data: {symbol}")
                # Polygon intraday data requires paid plan, so this will likely fail
                result = await self.polygon_client.get_intraday_data(symbol, interval)
                if result and 'error' not in result:
                    logger.info(f"Polygon intraday data retrieved successfully for {symbol}")
                    return result
            except Exception as e:
                logger.error(f"Polygon intraday data failed for {symbol}: {e}")
        
        # 2. Try Alpha Vantage
        if self.alpha_vantage_key:
            try:
                logger.info(f"Trying Alpha Vantage for intraday data: {symbol}")
                av_symbol = self._map_symbol_to_alpha_vantage(symbol)
                result = await self._get_alpha_vantage_intraday(av_symbol, interval)
                if result and 'error' not in result:
                    logger.info(f"Alpha Vantage intraday data retrieved successfully for {symbol}")
                    return result
            except Exception as e:
                logger.error(f"Alpha Vantage intraday data failed for {symbol}: {e}")
        
        # 3. Fallback to Yahoo Finance
        if self.yahoo_client:
            try:
                logger.info(f"Falling back to Yahoo Finance for intraday data: {symbol}")
                # Map interval to Yahoo Finance format
                interval_mapping = {
                    "60min": "1h",
                    "1h": "1h",
                    "30min": "30m",
                    "15min": "15m",
                    "5min": "5m",
                    "1min": "1m"
                }
                yahoo_interval = interval_mapping.get(interval, interval)
                # Use shorter period for intraday to avoid date range issues
                df = await self.yahoo_client.get_historical_data(symbol, period="5d", interval=yahoo_interval)
                if isinstance(df, pd.DataFrame) and not df.empty:
                    logger.info(f"Yahoo Finance intraday data retrieved successfully for {symbol}")
                    return df
            except Exception as e:
                logger.error(f"Yahoo Finance intraday data failed for {symbol}: {e}")
        
        logger.error(f"No intraday data available for {symbol}")
        return {'error': 'No intraday data available'}
    
    async def get_comprehensive_commodity_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive commodity analysis data."""
        try:
            logger.info(f"Fetching comprehensive commodity data for {symbol}")
            
            # Get current quote
            quote_data = await self.get_commodity_quote(symbol)
            
            # Check for error in quote data
            if isinstance(quote_data, dict) and 'error' in quote_data:
                logger.error(f"Quote data contains error: {quote_data}")
                return {'error': 'Failed to get quote data'}
            
            # Get daily historical data
            daily_data = await self.get_commodity_daily(symbol, "compact")
            
            # Check for error in daily data
            if isinstance(daily_data, pd.DataFrame) and daily_data.empty:
                logger.error(f"Daily data is empty for {symbol}")
            
            # Get intraday data
            intraday_data = await self.get_commodity_intraday_data(symbol, "60min")
            
            # Check for error in intraday data
            if isinstance(intraday_data, dict) and 'error' in intraday_data:
                logger.error(f"Intraday data contains error: {intraday_data}")
            
            # Get commodity news (placeholder for now)
            news_data = []
            
            # Process the data into a consistent format
            processed_data = {
                "symbol": symbol,
                "quote": self._process_quote_data(quote_data),
                "daily_data": self._process_daily_data(daily_data),
                "hourly_data": self._process_intraday_data(intraday_data),
                "news": news_data,
                "timestamp": datetime.now().isoformat(),
                "source": "Multi-source (NASDAQ/Alpha Vantage/FRED/Yahoo)"
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error in commodity analysis: {e}")
            return {"error": str(e)}
    
    def _process_quote_data(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process quote data into consistent format."""
        if "error" in quote_data:
            logger.error(f"Quote data contains error: {quote_data}")
            return {}
        
        logger.info(f"Processing quote data: {quote_data}")
        
        # Handle Alpha Vantage format
        if "Global Quote" in quote_data:
            global_quote = quote_data["Global Quote"]
            return {
                "symbol": global_quote.get("01. symbol", ""),
                "price": float(global_quote.get("05. price", 0)),
                "change": float(global_quote.get("09. change", 0)),
                "change_percent": global_quote.get("10. change percent", "0%").replace("%", ""),
                "volume": int(global_quote.get("06. volume", 0)),
                "latest_trading_day": global_quote.get("07. latest trading day", ""),
                "previous_close": float(global_quote.get("08. previous close", 0))
            }
        
        # Handle unified format (FRED, Yahoo Finance, Polygon)
        if "symbol" in quote_data:
            return {
                "symbol": quote_data.get("symbol", ""),
                "price": float(quote_data.get("price", 0)) if quote_data.get("price") is not None else 0,
                "change": float(quote_data.get("change", 0)) if quote_data.get("change") is not None else 0,
                "change_percent": quote_data.get("change_percent", "0%"),
                "volume": int(quote_data.get("volume", 0)) if quote_data.get("volume") is not None else 0,
                "latest_trading_day": quote_data.get("date", quote_data.get("timestamp", "")),
                "source": quote_data.get("source", "Unknown")
            }
        
        logger.warning(f"Unknown quote data format: {quote_data}")
        return {}
    
    def _process_daily_data(self, daily_data) -> List[Dict[str, Any]]:
        """Process daily data into consistent format."""
        # Handle pandas DataFrame (Yahoo Finance, Polygon)
        if isinstance(daily_data, pd.DataFrame):
            if daily_data.empty:
                logger.warning(f"Daily data DataFrame is empty")
                return []
            
            processed = []
            for index, row in daily_data.iterrows():
                try:
                    timestamp = int(index.timestamp() * 1000) if hasattr(index, 'timestamp') else int(time.time() * 1000)
                    processed.append({
                        "t": timestamp,
                        "o": float(row.get("Open", row.get("open", 0))),
                        "h": float(row.get("High", row.get("high", 0))),
                        "l": float(row.get("Low", row.get("low", 0))),
                        "c": float(row.get("Close", row.get("close", 0))),
                        "v": int(row.get("Volume", row.get("volume", 0)))
                    })
                except Exception as e:
                    logger.error(f"Error processing DataFrame row: {e}")
                    continue
            return processed
        
        # Handle dictionary format (Alpha Vantage)
        if isinstance(daily_data, dict):
            if "error" in daily_data:
                logger.error(f"Daily data contains error: {daily_data}")
                return []
            
            logger.info(f"Processing daily data keys: {list(daily_data.keys())}")
            time_series = daily_data.get("Time Series (Daily)", {})
            if not time_series:
                logger.warning(f"No Time Series (Daily) found in daily data: {daily_data}")
                return []
            
            processed = []
            for date_str, data in time_series.items():
                try:
                    timestamp = int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)
                    processed.append({
                        "t": timestamp,
                        "o": float(data.get("1. open", 0)),
                        "h": float(data.get("2. high", 0)),
                        "l": float(data.get("3. low", 0)),
                        "c": float(data.get("4. close", 0)),
                        "v": int(data.get("5. volume", 0))
                    })
                except (ValueError, KeyError) as e:
                    logger.error(f"Error processing daily data for {date_str}: {e}")
                    continue
            
            return sorted(processed, key=lambda x: x["t"], reverse=True)
        
        return []
    
    def _process_intraday_data(self, intraday_data) -> List[Dict[str, Any]]:
        """Process intraday data into consistent format."""
        # Handle pandas DataFrame (Yahoo Finance, Polygon)
        if isinstance(intraday_data, pd.DataFrame):
            if intraday_data.empty:
                return []
            
            processed = []
            for index, row in intraday_data.iterrows():
                try:
                    timestamp = int(index.timestamp() * 1000) if hasattr(index, 'timestamp') else int(time.time() * 1000)
                    processed.append({
                        "t": timestamp,
                        "o": float(row.get("Open", row.get("open", 0))),
                        "h": float(row.get("High", row.get("high", 0))),
                        "l": float(row.get("Low", row.get("low", 0))),
                        "c": float(row.get("Close", row.get("close", 0))),
                        "v": int(row.get("Volume", row.get("volume", 0)))
                    })
                except Exception as e:
                    logger.error(f"Error processing intraday DataFrame row: {e}")
                    continue
            return sorted(processed, key=lambda x: x["t"], reverse=True)
        
        # Handle dictionary format (Alpha Vantage)
        if isinstance(intraday_data, dict):
            if "error" in intraday_data:
                return []
            
            # Find the time series key
            time_series_key = None
            for key in intraday_data.keys():
                if "Time Series" in key:
                    time_series_key = key
                    break
            
            if not time_series_key:
                return []
            
            time_series = intraday_data.get(time_series_key, {})
            processed = []
            
            for datetime_str, data in time_series.items():
                try:
                    timestamp = int(datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
                    processed.append({
                        "t": timestamp,
                        "o": float(data.get("1. open", 0)),
                        "h": float(data.get("2. high", 0)),
                        "l": float(data.get("3. low", 0)),
                        "c": float(data.get("4. close", 0)),
                        "v": int(data.get("5. volume", 0))
                    })
                except (ValueError, KeyError) as e:
                    logger.warning(f"Error processing intraday data for {datetime_str}: {e}")
                    continue
            
            return sorted(processed, key=lambda x: x["t"], reverse=True)
        
        return []
    
    def _process_news_data(self, news_data: List) -> List[Dict[str, Any]]:
        """Process news data into consistent format."""
        if not news_data or not isinstance(news_data, list):
            return []
        
        processed = []
        for article in news_data[:5]:  # Top 5 articles
            if isinstance(article, dict):
                processed.append({
                    "title": article.get("title", ""),
                    "summary": article.get("summary", ""),
                    "url": article.get("url", ""),
                    "time_published": article.get("time_published", ""),
                    "source": article.get("source", ""),
                    "sentiment": article.get("overall_sentiment_label", "neutral")
                })
        
        return processed
    
    def get_major_commodities(self) -> List[Dict[str, str]]:
        """Get list of major commodities with their symbols."""
        return [
            # Energy
            {"name": "Crude Oil WTI", "symbol": "CL=F", "category": "Energy"},
            {"name": "Brent Crude Oil", "symbol": "BZ=F", "category": "Energy"},
            {"name": "Natural Gas", "symbol": "NG=F", "category": "Energy"},
            {"name": "Heating Oil", "symbol": "HO=F", "category": "Energy"},
            {"name": "Gasoline", "symbol": "RB=F", "category": "Energy"},
            
            # Precious Metals
            {"name": "Gold", "symbol": "GC=F", "category": "Precious Metals"},
            {"name": "Silver", "symbol": "SI=F", "category": "Precious Metals"},
            {"name": "Platinum", "symbol": "PL=F", "category": "Precious Metals"},
            {"name": "Palladium", "symbol": "PA=F", "category": "Precious Metals"},
            
            # Base Metals
            {"name": "Copper", "symbol": "HG=F", "category": "Base Metals"},
            {"name": "Aluminum", "symbol": "ALI=F", "category": "Base Metals"},
            
            # Agriculture
            {"name": "Corn", "symbol": "ZC=F", "category": "Agriculture"},
            {"name": "Wheat", "symbol": "ZW=F", "category": "Agriculture"},
            {"name": "Soybeans", "symbol": "ZS=F", "category": "Agriculture"},
            {"name": "Sugar", "symbol": "SB=F", "category": "Agriculture"},
            {"name": "Coffee", "symbol": "KC=F", "category": "Agriculture"},
            {"name": "Cotton", "symbol": "CT=F", "category": "Agriculture"},
            
            # Livestock
            {"name": "Live Cattle", "symbol": "LE=F", "category": "Livestock"},
            {"name": "Lean Hogs", "symbol": "HE=F", "category": "Livestock"}
        ]
