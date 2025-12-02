"""Binance API client for cryptocurrency data fetching."""

import asyncio
import logging
import os
import time
import json
import pickle
import fcntl
import tempfile
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException
import pytz

from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class BinanceClient:
    """Binance API client for fetching cryptocurrency market data."""
    
    def __init__(self, config: MarketResearcherConfig):
        """Initialize Binance client with configuration."""
        self.config = config
        self.client = None
        
    async def initialize(self):
        """Initialize Binance client with API credentials."""
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize Binance client with API credentials."""
        try:
            if self.config.binance_api_key and self.config.binance_secret_key:
                self.client = Client(
                    api_key=self.config.binance_api_key,
                    api_secret=self.config.binance_secret_key,
                    testnet=self.config.binance_testnet
                )
                logger.info("Binance client initialized with API credentials")
            else:
                # Initialize without credentials for public data only
                self.client = Client()
                logger.info("Binance client initialized for public data only")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise
    
    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            raise
    
    def get_24hr_ticker(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get 24hr ticker statistics for a symbol with caching."""
        import time
        import os
        import json
        
        cache_file = f"cache/{symbol}_ticker.json"
        cache_duration = 300  # 5 minutes in seconds
        
        # Check if cache exists and is fresh (unless force refresh)
        if not force_refresh and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with self._safe_file_read(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached ticker data for {symbol} (age: {cache_age:.1f}s)")
                        return cached_data
            except Exception as e:
                logger.warning(f"Error reading ticker cache for {symbol}: {e}")
        
        # Fetch fresh data from API
        try:
            ticker = self.client.get_ticker(symbol=symbol)
            result = {
                'symbol': ticker['symbol'],
                'price': float(ticker['lastPrice']),
                'priceChange': float(ticker['priceChange']),
                'priceChangePercent': float(ticker['priceChangePercent']),
                'volume': float(ticker['volume']),
                'quoteVolume': float(ticker['quoteVolume']),
                'high': float(ticker['highPrice']),
                'low': float(ticker['lowPrice']),
                'open': float(ticker['openPrice']),
                'count': int(ticker['count']),
                'timestamp': time.time()
            }
            
            # Save to cache
            try:
                os.makedirs('cache', exist_ok=True)
                with self._safe_file_write(cache_file, 'w') as f:
                    json.dump(result, f)
                logger.info(f"Cached fresh ticker data for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to cache ticker for {symbol}: {e}")
            
            return result
            
        except BinanceAPIException as e:
            logger.error(f"Error fetching 24hr ticker for {symbol}: {e}")
            raise
    
    def get_historical_klines(
        self, 
        symbol: str, 
        interval: str, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """Get historical kline/candlestick data with incremental caching."""
        import pickle
        import os
        import time
        
        cache_file = f"cache/{symbol}_{interval}_{limit}.pkl"
        
        # Try incremental update if cache exists and use_cache is True
        if use_cache and os.path.exists(cache_file):
            try:
                # Load existing cache
                with self._safe_file_read(cache_file, 'rb') as f:
                    cached_df = pickle.load(f)
                
                if not cached_df.empty:
                    # Get the latest timestamp from cache
                    latest_cached_time = cached_df.index.max()
                    
                    # Check if cache is recent enough (within 1 hour for most intervals)
                    cache_age_hours = (datetime.now() - latest_cached_time).total_seconds() / 3600
                    
                    # Determine if we need new data
                    interval_minutes = self._get_interval_minutes(interval)
                    needs_update = cache_age_hours > (interval_minutes / 60)
                    
                    if not needs_update:
                        logger.info(f"Using fresh cached data for {symbol}_{interval} (age: {cache_age_hours:.1f}h)")
                        return cached_df
                    
                    # Fetch only new data since latest cached timestamp
                    new_start_time = latest_cached_time + pd.Timedelta(minutes=interval_minutes)
                    logger.info(f"Fetching incremental data for {symbol} from {new_start_time}")
                    
                    new_df = self._fetch_klines_raw(symbol, interval, new_start_time, end_time, limit)
                    
                    if not new_df.empty:
                        # Combine cached and new data, removing duplicates
                        combined_df = pd.concat([cached_df, new_df]).drop_duplicates()
                        combined_df = combined_df.sort_index()
                        
                        # Keep only the most recent 'limit' records
                        if len(combined_df) > limit:
                            combined_df = combined_df.tail(limit)
                        
                        # Update cache with combined data
                        self._save_klines_cache(cache_file, combined_df)
                        logger.info(f"Updated cache with {len(new_df)} new candles for {symbol}")
                        return combined_df
                    else:
                        logger.info(f"No new data available for {symbol}, using cache")
                        return cached_df
                        
            except Exception as e:
                logger.warning(f"Cache read/update error for {symbol}: {e}, fetching fresh data")
        
        # Fetch complete fresh data (fallback or initial load)
        logger.info(f"Fetching fresh complete dataset for {symbol}_{interval}")
        df = self._fetch_klines_raw(symbol, interval, start_time, end_time, limit)
        
        # Save to cache if use_cache is True
        if use_cache and not df.empty:
            self._save_klines_cache(cache_file, df)
            
        return df
    
    def _get_interval_minutes(self, interval: str) -> int:
        """Convert interval string to minutes."""
        interval_map = {
            '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
            '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
            '1d': 1440, '3d': 4320, '1w': 10080, '1M': 43200
        }
        return interval_map.get(interval, 60)
    
    def _fetch_klines_raw(
        self, 
        symbol: str, 
        interval: str, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 500
    ) -> pd.DataFrame:
        """Fetch raw klines data from Binance API."""
        try:
            # Convert datetime to timestamp if provided
            start_str = None
            end_str = None
            
            if start_time:
                start_str = str(int(start_time.timestamp() * 1000))
            if end_time:
                end_str = str(int(end_time.timestamp() * 1000))
            
            klines = self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_str,
                end_str=end_str,
                limit=limit
            )
            
            if not klines:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            # Convert price and volume columns to float
            price_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume']
            for col in price_columns:
                df[col] = df[col].astype(float)
            
            df['number_of_trades'] = df['number_of_trades'].astype(int)
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except BinanceAPIException as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return pd.DataFrame()
    
    def _safe_file_read(self, file_path: str, mode: str = 'r'):
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
    
    def _safe_file_write(self, file_path: str, mode: str = 'w'):
        """Context manager for safe file writing with locking."""
        class SafeFileWriter:
            def __init__(self, file_path, mode):
                self.file_path = file_path
                self.mode = mode
                self.file = None
                self.temp_file = None
                
            def __enter__(self):
                # Create temporary file in same directory
                dir_path = os.path.dirname(self.file_path) or '.'
                self.temp_file = tempfile.NamedTemporaryFile(
                    mode=self.mode, 
                    dir=dir_path, 
                    delete=False,
                    prefix=os.path.basename(self.file_path) + '.tmp'
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
    
    def _save_klines_cache(self, cache_file: str, df: pd.DataFrame):
        """Save klines DataFrame to cache."""
        try:
            os.makedirs('cache', exist_ok=True)
            with self._safe_file_write(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_file}: {e}")
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book depth for a symbol."""
        try:
            depth = self.client.get_order_book(symbol=symbol, limit=limit)
            return {
                'symbol': symbol,
                'bids': [(float(price), float(qty)) for price, qty in depth['bids']],
                'asks': [(float(price), float(qty)) for price, qty in depth['asks']],
                'last_update_id': depth['lastUpdateId']
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            raise
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trades for a symbol."""
        try:
            trades = self.client.get_recent_trades(symbol=symbol, limit=limit)
            return [{
                'id': trade['id'],
                'price': float(trade['price']),
                'qty': float(trade['qty']),
                'time': datetime.fromtimestamp(trade['time'] / 1000, tz=pytz.UTC),
                'is_buyer_maker': trade['isBuyerMaker']
            } for trade in trades]
        except BinanceAPIException as e:
            logger.error(f"Error fetching recent trades for {symbol}: {e}")
            raise
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information."""
        try:
            info = self.client.get_exchange_info()
            if symbol:
                # Find specific symbol info
                for symbol_info in info['symbols']:
                    if symbol_info['symbol'] == symbol:
                        return symbol_info
                raise ValueError(f"Symbol {symbol} not found")
            return info
        except BinanceAPIException as e:
            logger.error(f"Error fetching exchange info: {e}")
            raise
    
    def get_all_tickers(self) -> List[Dict[str, Any]]:
        """Get price ticker for all symbols."""
        try:
            tickers = self.client.get_all_tickers()
            return [{
                'symbol': ticker['symbol'],
                'price': float(ticker['price'])
            } for ticker in tickers]
        except BinanceAPIException as e:
            logger.error(f"Error fetching all tickers: {e}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information (requires API credentials)."""
        if not self.config.binance_api_key:
            raise ValueError("API credentials required for account information")
        
        try:
            account = self.client.get_account()
            return {
                'maker_commission': account['makerCommission'],
                'taker_commission': account['takerCommission'],
                'buyer_commission': account['buyerCommission'],
                'seller_commission': account['sellerCommission'],
                'can_trade': account['canTrade'],
                'can_withdraw': account['canWithdraw'],
                'can_deposit': account['canDeposit'],
                'balances': [{
                    'asset': balance['asset'],
                    'free': float(balance['free']),
                    'locked': float(balance['locked'])
                } for balance in account['balances'] if float(balance['free']) > 0 or float(balance['locked']) > 0]
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching account info: {e}")
            raise
    
    async def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists on Binance."""
        try:
            self.client.get_symbol_ticker(symbol=symbol)
            return True
        except BinanceAPIException:
            return False
    
    def get_positions(self) -> Dict[str, Any]:
        """Get current positions from Binance account."""
        if not self.config.binance_api_key:
            raise ValueError("API credentials required for position information")
        
        try:
            account = self.client.get_account()
            positions = {}
            
            for balance in account['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0 and asset != 'USDT':  # Exclude base currency
                    # Handle special cases for symbol mapping
                    if asset == 'ETHW':
                        symbol = 'ETHUSDT'  # Map ETHW to ETH
                        asset = 'ETH'
                    else:
                        symbol = f"{asset}USDT"
                    
                    positions[symbol] = {
                        'asset': asset,
                        'free': free,
                        'locked': locked,
                        'total': total,
                        'symbol': symbol
                    }
            
            return {
                'success': True,
                'positions': positions,
                'account_type': account.get('accountType', 'SPOT'),
                'timestamp': datetime.now().isoformat()
            }
            
        except BinanceAPIException as e:
            logger.error(f"Error fetching positions: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_supported_intervals(self) -> List[str]:
        """Get list of supported kline intervals."""
        return [
            '1m', '3m', '5m', '15m', '30m',
            '1h', '2h', '4h', '6h', '8h', '12h',
            '1d', '3d', '1w', '1M'
        ]
