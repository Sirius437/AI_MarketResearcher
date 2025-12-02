"""
Yahoo Finance API client for global stock data.
Provides centralized access to Yahoo Finance with caching and rate limiting.
"""

import asyncio
import logging
import time
import json
import os
import pickle
import fcntl
import tempfile
import requests
import re
import feedparser
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor

try:
    from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Client for Yahoo Finance API with caching and rate limiting."""
    
    def __init__(self):
        """Initialize Yahoo Finance client."""
        self.session = None
        
        # Rate limiting (Conservative approach)
        self.rate_limit = 10  # requests per minute
        self.rate_window = 60  # seconds
        self.request_times = []
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize Yahoo Finance News Tool if available
        self.news_tool = YahooFinanceNewsTool() if LANGCHAIN_AVAILABLE else None
        
    async def initialize(self):
        """Initialize async resources (compatibility method)."""
        # Yahoo Finance client doesn't need async initialization
        pass
        
    def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        now = time.time()
        
        # Remove requests older than rate window
        self.request_times = [t for t in self.request_times if now - t < self.rate_window]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.rate_limit:
            sleep_time = self.rate_window - (now - self.request_times[0]) + 1
            logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
            
        # Record this request
        self.request_times.append(now)
    
    async def get_stock_info(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get stock info with caching."""
        cache_file = f"cache/{symbol}_info_yahoo.json"
        cache_duration = 3600  # 1 hour
        
        # Check cache first
        if not force_refresh and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with self._safe_file_read(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached stock info for {symbol} (age: {cache_age:.1f}s)")
                        return cached_data
            except Exception as e:
                logger.warning(f"Cache read error for {symbol}: {e}")
        
        # Fetch fresh data
        def _fetch_info():
            self._rate_limit_check()
            ticker = yf.Ticker(symbol)
            return ticker.info
        
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(self.executor, _fetch_info)
            
            if info and 'symbol' in info:
                # Add timestamp and cache
                info['timestamp'] = time.time()
                try:
                    os.makedirs('cache', exist_ok=True)
                    with self._safe_file_write(cache_file, 'w') as f:
                        json.dump(info, f, default=str)
                    logger.info(f"Cached stock info for {symbol}")
                except Exception as e:
                    logger.warning(f"Cache write error for {symbol}: {e}")
                
                return info
            else:
                return {'error': f'Stock {symbol} not found'}
                
        except Exception as e:
            logger.error(f"Error fetching stock info for {symbol}: {e}")
            return {'error': str(e)}
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get current quote data for a symbol."""
        try:
            def _get_quote():
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return {
                    'regularMarketPrice': info.get('regularMarketPrice', info.get('currentPrice')),
                    'regularMarketChange': info.get('regularMarketChange'),
                    'regularMarketChangePercent': info.get('regularMarketChangePercent'),
                    'regularMarketVolume': info.get('regularMarketVolume', info.get('volume')),
                    'symbol': symbol
                }
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, _get_quote)
            return result
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {e}")
            return {'error': str(e)}
    
    async def get_historical_data(self, symbol: str, period: str = "1y", 
                                interval: str = "1d", use_cache: bool = True) -> pd.DataFrame:
        """Get historical data with incremental caching."""
        cache_file = f"cache/{symbol}_{period}_{interval}_yahoo.pkl"
        
        # Try incremental update if cache exists
        if use_cache and os.path.exists(cache_file):
            try:
                with self._safe_file_read(cache_file, 'rb') as f:
                    cached_df = pickle.load(f)
                
                if not cached_df.empty:
                    # Get latest timestamp from cache
                    latest_cached_time = cached_df.index.max()
                    
                    # Check if cache is recent enough
                    interval_hours = {'1m': 1/60, '2m': 2/60, '5m': 5/60, '15m': 15/60, 
                                    '30m': 0.5, '60m': 1, '90m': 1.5, '1h': 1, '1d': 24, 
                                    '5d': 120, '1wk': 168, '1mo': 720, '3mo': 2160}
                    
                    # Handle timezone-aware timestamps from pandas
                    now = datetime.now()
                    if hasattr(latest_cached_time, 'tz_localize'):
                        # Convert timezone-aware to naive for comparison
                        latest_cached_time = latest_cached_time.tz_localize(None) if latest_cached_time.tz is not None else latest_cached_time
                    elif hasattr(latest_cached_time, 'to_pydatetime'):
                        latest_cached_time = latest_cached_time.to_pydatetime().replace(tzinfo=None)
                    elif hasattr(latest_cached_time, 'tz'):
                        # Handle pandas Timestamp with timezone
                        latest_cached_time = pd.Timestamp(latest_cached_time).tz_localize(None) if latest_cached_time.tz is not None else latest_cached_time
                    
                    cache_age_hours = (now - latest_cached_time).total_seconds() / 3600
                    expected_interval = interval_hours.get(interval, 24)
                    
                    if cache_age_hours < expected_interval:
                        logger.info(f"Using cached historical data for {symbol} (age: {cache_age_hours:.1f}h)")
                        return cached_df
                    
                    # Fetch only new data since latest cached timestamp
                    # Ensure start_date is timezone-naive for yfinance
                    start_date = latest_cached_time + pd.Timedelta(days=1)
                    if hasattr(start_date, 'tz_localize') and start_date.tz is not None:
                        start_date = start_date.tz_localize(None)
                    logger.info(f"Fetching incremental data for {symbol} from {start_date}")
                    
                    new_df = await self._fetch_historical_raw(symbol, start=start_date, interval=interval)
                    
                    if not new_df.empty:
                        # Combine cached and new data
                        combined_df = pd.concat([cached_df, new_df]).drop_duplicates()
                        combined_df = combined_df.sort_index()
                        
                        # Keep reasonable amount of data based on period
                        period_limits = {'1d': 1, '5d': 5, '1mo': 30, '3mo': 90, 
                                       '6mo': 180, '1y': 365, '2y': 730, '5y': 1825, '10y': 3650}
                        limit_days = period_limits.get(period, 365)
                        cutoff_date = datetime.now() - timedelta(days=limit_days)
                        
                        # Handle timezone-aware index for filtering
                        if hasattr(combined_df.index, 'tz') and combined_df.index.tz is not None:
                            cutoff_date = pd.Timestamp(cutoff_date).tz_localize(combined_df.index.tz)
                        
                        combined_df = combined_df[combined_df.index >= cutoff_date]
                        
                        # Save updated cache
                        self._save_historical_cache(cache_file, combined_df)
                        logger.info(f"Updated cache with {len(new_df)} new records for {symbol}")
                        return combined_df
                    else:
                        return cached_df
                        
            except Exception as e:
                logger.warning(f"Historical cache error for {symbol}: {e}")
        
        # Fetch complete fresh data
        df = await self._fetch_historical_raw(symbol, period=period, interval=interval)
        
        # Save to cache
        if use_cache and not df.empty:
            self._save_historical_cache(cache_file, df)
            
        return df
    
    async def _fetch_historical_raw(self, symbol: str, period: str = None, 
                                  start: datetime = None, end: datetime = None,
                                  interval: str = "1d") -> pd.DataFrame:
        """Fetch raw historical data from Yahoo Finance."""
        def _fetch():
            self._rate_limit_check()
            # Ensure symbol is a string to prevent 'int' object has no attribute 'lower' error
            symbol_str = str(symbol) if symbol is not None else ""
            ticker = yf.Ticker(symbol_str)
            
            if start and end:
                return ticker.history(start=start, end=end, interval=interval)
            elif start:
                return ticker.history(start=start, interval=interval)
            elif period:
                return ticker.history(period=period, interval=interval)
            else:
                return ticker.history(period="1y", interval=interval)
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(self.executor, _fetch)
            return df if not df.empty else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
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
    
    def _save_historical_cache(self, cache_file: str, df: pd.DataFrame):
        """Save historical DataFrame to cache."""
        try:
            os.makedirs('cache', exist_ok=True)
            with self._safe_file_write(cache_file, 'wb') as f:
                pickle.dump(df, f)
        except Exception as e:
            logger.warning(f"Failed to save historical cache {cache_file}: {e}")
    
    async def get_news(self, symbol: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get news with caching."""
        cache_file = f"cache/{symbol}_news_yahoo.json"
        cache_duration = 1800  # 30 minutes
        
        # Check cache first
        if use_cache and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with self._safe_file_read(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached news for {symbol} (age: {cache_age:.1f}s)")
                        return cached_data.get('articles', [])
            except Exception as e:
                logger.warning(f"News cache error for {symbol}: {e}")
        
        # Fetch fresh news
        def _fetch_news():
            self._rate_limit_check()
            
            # Method 1: Try RSS feed approach
            try:
                # Yahoo Finance RSS feed for company news
                rss_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
                
                logger.info(f"Fetching RSS feed for {symbol}: {rss_url}")
                feed = feedparser.parse(rss_url)
                
                if feed.entries:
                    valid_news = []
                    for entry in feed.entries[:10]:
                        headline = entry.get('title', '').strip()
                        if headline and len(headline) > 10:
                            # Parse published date
                            timestamp = int(time.time())
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                try:
                                    parsed_time = int(time.mktime(entry.published_parsed))
                                    # Only use parsed time if it's reasonable (not in far future)
                                    current_time = int(time.time())
                                    if parsed_time <= current_time + 86400:  # Not more than 1 day in future
                                        timestamp = parsed_time
                                except:
                                    pass
                            
                            valid_news.append({
                                'headline': headline,
                                'datetime': timestamp,
                                'source': entry.get('source', 'Yahoo Finance'),
                                'url': entry.get('link', '')
                            })
                    
                    if valid_news:
                        logger.info(f"RSS feed extracted {len(valid_news)} news articles for {symbol}")
                        return valid_news
                
            except Exception as e:
                logger.warning(f"RSS feed failed for {symbol}: {e}")
            
            # Method 2: Use LangChain YahooFinanceNewsTool if available
            if self.news_tool:
                try:
                    logger.info(f"Using LangChain YahooFinanceNewsTool for {symbol}")
                    news_text = self.news_tool.invoke(symbol)
                    
                    if news_text and "No news found" not in news_text:
                        # Parse the news text into structured format
                        valid_news = []
                        current_time = int(time.time())
                        
                        # Split news by double newlines to separate articles
                        articles = news_text.split('\n\n')
                        
                        for i, article in enumerate(articles[:10]):
                            if len(article.strip()) > 20:  # Filter out very short content
                                # Extract headline (first line) and summary
                                lines = article.strip().split('\n')
                                headline = lines[0].strip()
                                
                                if headline and len(headline) > 10:
                                    valid_news.append({
                                        'headline': headline,
                                        'datetime': current_time - (i * 1800),  # Stagger by 30 minutes
                                        'source': 'Yahoo Finance',
                                        'url': ''
                                    })
                        
                        if valid_news:
                            logger.info(f"LangChain tool extracted {len(valid_news)} news articles for {symbol}")
                            return valid_news
                    else:
                        logger.info(f"LangChain tool found no news for {symbol}")
                        
                except Exception as e:
                    logger.warning(f"LangChain YahooFinanceNewsTool failed for {symbol}: {e}")
            
            # Method 3: Fallback to yfinance library
            try:
                ticker = yf.Ticker(symbol)
                news_data = ticker.news if hasattr(ticker, 'news') and ticker.news else []
                
                # Process yfinance data
                valid_news = []
                for article in news_data[:20]:
                    if isinstance(article, dict):
                        headline = (article.get('title') or 
                                  article.get('headline') or 
                                  article.get('summary', ''))
                        
                        if headline and headline not in ['N/A', '']:
                            timestamp = (article.get('providerPublishTime') or 
                                       article.get('publishedAt') or
                                       article.get('datetime') or 
                                       int(time.time()))
                            
                            source = 'Yahoo Finance'
                            if 'publisher' in article:
                                if isinstance(article['publisher'], dict):
                                    source = article['publisher'].get('name', 'Yahoo Finance')
                                else:
                                    source = str(article['publisher'])
                            elif 'source' in article:
                                source = article['source']
                            
                            valid_news.append({
                                'headline': headline,
                                'datetime': timestamp,
                                'source': source,
                                'url': article.get('link', article.get('url', ''))
                            })
                
                if valid_news:
                    logger.info(f"yfinance extracted {len(valid_news)} news articles for {symbol}")
                else:
                    logger.info(f"No valid news found for {symbol}")
                
                return valid_news
                
            except Exception as e:
                logger.warning(f"yfinance news fallback failed for {symbol}: {e}")
                return []
        
        try:
            loop = asyncio.get_event_loop()
            news = await loop.run_in_executor(self.executor, _fetch_news)
            
            # Cache the result
            if use_cache:
                try:
                    os.makedirs('cache', exist_ok=True)
                    cache_data = {'articles': news, 'timestamp': time.time()}
                    with self._safe_file_write(cache_file, 'w') as f:
                        json.dump(cache_data, f, default=str)
                    logger.info(f"Cached news for {symbol}")
                except Exception as e:
                    logger.warning(f"Failed to cache news for {symbol}: {e}")
            
            return news
            
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return []
    
    async def get_financials(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get financial statements with caching."""
        cache_file = f"cache/{symbol}_financials_yahoo.json"
        cache_duration = 86400  # 24 hours
        
        # Check cache first
        if use_cache and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with self._safe_file_read(cache_file, 'r') as f:
                        content = f.read().strip()
                        if content:  # Only parse if file has content
                            cached_data = json.loads(content)
                            logger.info(f"Using cached financials for {symbol} (age: {cache_age:.1f}s)")
                            return cached_data
                        else:
                            logger.warning(f"Empty financials cache file for {symbol}, removing")
                            os.remove(cache_file)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.warning(f"Financials cache JSON error for {symbol}: {e}, removing corrupted cache")
                try:
                    os.remove(cache_file)
                except:
                    pass
            except Exception as e:
                logger.warning(f"Financials cache error for {symbol}: {e}")
        
        # Fetch fresh financials
        def _fetch_financials():
            self._rate_limit_check()
            ticker = yf.Ticker(symbol)
            
            def _safe_dataframe_to_dict(df):
                """Safely convert DataFrame to dict with string keys."""
                if df is None or df.empty:
                    return {}
                try:
                    # Convert DataFrame to dict and ensure all keys are strings
                    df_dict = df.to_dict()
                    # Convert any Timestamp keys to strings
                    clean_dict = {}
                    for col_key, col_data in df_dict.items():
                        clean_col_data = {}
                        for row_key, value in col_data.items():
                            # Convert Timestamp keys to string
                            str_key = str(row_key) if hasattr(row_key, 'strftime') else str(row_key)
                            # Handle NaN/None values
                            clean_value = None if pd.isna(value) else float(value) if isinstance(value, (int, float)) else str(value)
                            clean_col_data[str_key] = clean_value
                        clean_dict[str(col_key)] = clean_col_data
                    return clean_dict
                except Exception as e:
                    logger.warning(f"Error converting DataFrame to dict: {e}")
                    return {}
            
            try:
                return {
                    'income_stmt': _safe_dataframe_to_dict(ticker.income_stmt) if hasattr(ticker, 'income_stmt') else {},
                    'balance_sheet': _safe_dataframe_to_dict(ticker.balance_sheet) if hasattr(ticker, 'balance_sheet') else {},
                    'cash_flow': _safe_dataframe_to_dict(ticker.cashflow) if hasattr(ticker, 'cashflow') else {},
                    'quarterly_income_stmt': _safe_dataframe_to_dict(ticker.quarterly_income_stmt) if hasattr(ticker, 'quarterly_income_stmt') else {},
                    'quarterly_balance_sheet': _safe_dataframe_to_dict(ticker.quarterly_balance_sheet) if hasattr(ticker, 'quarterly_balance_sheet') else {},
                    'quarterly_cashflow': _safe_dataframe_to_dict(ticker.quarterly_cashflow) if hasattr(ticker, 'quarterly_cashflow') else {}
                }
            except Exception as e:
                logger.warning(f"Error fetching financials for {symbol}: {e}")
                return {}
        
        try:
            loop = asyncio.get_event_loop()
            financials = await loop.run_in_executor(self.executor, _fetch_financials)
            
            # Cache the result
            if use_cache and financials:
                try:
                    os.makedirs('cache', exist_ok=True)
                    financials['timestamp'] = time.time()
                    with self._safe_file_write(cache_file, 'w') as f:
                        json.dump(financials, f)
                    logger.info(f"Cached financials for {symbol}")
                except Exception as e:
                    logger.warning(f"Failed to cache financials for {symbol}: {e}")
            
            return financials
            
        except Exception as e:
            logger.error(f"Error fetching financials for {symbol}: {e}")
            return {}
    
    async def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive stock analysis including info, historical data, and news."""
        logger.info(f"Fetching comprehensive Yahoo Finance data for {symbol}")
        
        try:
            # Get all data concurrently
            info_task = self.get_stock_info(symbol)
            hist_task = self.get_historical_data(symbol, period="1y")
            news_task = self.get_news(symbol)
            financials_task = self.get_financials(symbol)
            
            info, hist, news, financials = await asyncio.gather(
                info_task, hist_task, news_task, financials_task,
                return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(info, Exception):
                info = {'error': str(info)}
            if isinstance(hist, Exception):
                hist = pd.DataFrame()
            if isinstance(news, Exception):
                news = []
            if isinstance(financials, Exception):
                financials = {}
            
            result = {
                'symbol': symbol,
                'info': info,
                'historical_data': hist.to_dict() if not hist.empty else {},
                'news': news,
                'financials': financials,
                'timestamp': datetime.now().isoformat(),
                'source': 'Yahoo Finance'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive Yahoo Finance analysis: {e}")
            return {'error': str(e)}
    
    def get_supported_exchanges(self) -> List[str]:
        """Get list of major exchanges supported by Yahoo Finance."""
        return [
            # US
            "NYSE", "NASDAQ", "AMEX",
            # Europe
            "LSE", "EPA", "ETR", "AMS", "SWX", "BIT", "MCE", "ELI",
            # Asia-Pacific
            "TSE", "TYO", "HKG", "SHA", "SHE", "BSE", "NSE", "ASX", "TSX",
            # Others
            "JSE", "SAO", "MEX", "TAE", "DFM", "ADX"
        ]
    
    def format_symbol_for_exchange(self, symbol: str, exchange: str) -> str:
        """Format symbol for specific exchange."""
        exchange_suffixes = {
            'LSE': '.L',      # London Stock Exchange
            'EPA': '.PA',     # Euronext Paris
            'ETR': '.DE',     # XETRA (Germany)
            'AMS': '.AS',     # Euronext Amsterdam
            'SWX': '.SW',     # SIX Swiss Exchange
            'BIT': '.MI',     # Borsa Italiana
            'TSE': '.TO',     # Toronto Stock Exchange
            'TYO': '.T',      # Tokyo Stock Exchange
            'HKG': '.HK',     # Hong Kong Stock Exchange
            'ASX': '.AX',     # Australian Securities Exchange
            'BSE': '.BO',     # Bombay Stock Exchange
            'NSE': '.NS',     # National Stock Exchange of India
            'JSE': '.JO',     # Johannesburg Stock Exchange
            'SAO': '.SA',     # B3 (Brazil)
        }
        
        suffix = exchange_suffixes.get(exchange, '')
        if suffix and not symbol.endswith(suffix):
            return f"{symbol}{suffix}"
        return symbol
    
    async def close(self):
        """Close the client and cleanup resources."""
        if self.executor:
            self.executor.shutdown(wait=True)
    
    def __del__(self):
        """Cleanup on deletion."""
        if hasattr(self, 'executor') and self.executor:
            self.executor.shutdown(wait=False)
