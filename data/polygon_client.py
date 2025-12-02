"""
Polygon.io API client using official Python SDK.
Supports stocks, indices, forex, crypto, and options.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from polygon import RESTClient
from polygon.rest.models import Agg

logger = logging.getLogger(__name__)


class PolygonClient:
    """Client for Polygon.io API using official Python SDK.
    
    FREE TIER LIMITATIONS:
    - Only historical aggregates data available
    - NO real-time quotes, trades, or forex data
    - Severe rate limiting (5 requests/minute)
    - Most reference endpoints require paid plan
    """
    
    def __init__(self, api_key: str):
        """Initialize Polygon client with API key."""
        self.api_key = api_key
        self.client = RESTClient(api_key)
        
        # Rate limiting (Free tier: 5 requests per minute - VERY restrictive)
        self.rate_limit = 5  # requests per minute
        self.rate_window = 60  # seconds
        self.request_times = []
        
        # Asset type mappings for different endpoints
        self.asset_types = {
            'stocks': 'stocks',
            'indices': 'indices', 
            'forex': 'forex',
            'crypto': 'crypto',
            'options': 'options'
        }
        
        logger.warning("Polygon Free Tier has severe limitations - only historical data available")
        
    async def initialize(self):
        """Initialize client (no-op for SDK)."""
        pass
        
    async def close(self):
        """Close client (no-op for SDK)."""
        pass
    
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
    
    def _detect_asset_type(self, symbol: str) -> str:
        """Detect asset type from symbol format."""
        if '/' in symbol or 'C:' in symbol:
            return 'forex'
        elif symbol.startswith('I:'):
            return 'indices'
        elif symbol.startswith('X:'):
            return 'crypto'
        elif symbol.startswith('O:'):
            return 'options'
        else:
            return 'stocks'
    
    async def get_quote(self, symbol: str, asset_type: str = None) -> Dict[str, Any]:
        """Get current quote - NOT AVAILABLE in free tier."""
        return {
            'error': 'Real-time quotes not available in Polygon free tier',
            'upgrade_message': 'Please upgrade your plan at https://polygon.io/pricing',
            'symbol': symbol,
            'source': 'Polygon'
        }
    
    async def get_last_quote(self, symbol: str, asset_type: str = None) -> Dict[str, Any]:
        """Get last quote - NOT AVAILABLE in free tier."""
        return await self.get_quote(symbol, asset_type)
    
    async def get_aggregates(self, symbol: str, multiplier: int = 1, timespan: str = "day", 
                           start_date: str = None, end_date: str = None, 
                           asset_type: str = None, limit: int = 50000) -> pd.DataFrame:
        """Get aggregated historical data using official SDK."""
        await self._rate_limit_check()
        
        if not asset_type:
            asset_type = self._detect_asset_type(symbol)
        
        # Default to 1 year of data if no dates specified
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Clean symbol for API call
        clean_symbol = symbol.replace('=F', '')
        
        try:
            # Use official SDK's get_aggs method
            aggs = self.client.get_aggs(
                ticker=clean_symbol,
                multiplier=multiplier,
                timespan=timespan,
                from_=start_date,
                to=end_date,
                adjusted=True,
                sort="asc",
                limit=limit
            )
            
            if aggs:
                # Convert to pandas DataFrame
                df_data = []
                for agg in aggs:
                    # Handle timestamp conversion
                    if hasattr(agg, 'timestamp'):
                        date = pd.to_datetime(agg.timestamp, unit='ms').date()
                    else:
                        continue
                        
                    df_data.append({
                        'Date': date,
                        'Open': agg.open,
                        'High': agg.high,
                        'Low': agg.low,
                        'Close': agg.close,
                        'Volume': getattr(agg, 'volume', 0),
                        'VWAP': getattr(agg, 'vwap', None),
                        'Transactions': getattr(agg, 'transactions', 0)
                    })
                
                if df_data:
                    df = pd.DataFrame(df_data)
                    df.set_index('Date', inplace=True)
                    df = df.sort_index()
                    logger.info(f"Retrieved {len(df)} {timespan} bars for {symbol} from {start_date} to {end_date}")
                    return df
                else:
                    logger.warning(f"No aggregate data found for {symbol}")
                    return pd.DataFrame()
            else:
                logger.warning(f"No aggregate data for {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Polygon aggregates request failed for {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_historical_data(self, symbol: str, start_date: str = None, end_date: str = None, 
                                timespan: str = "day", limit: int = 365) -> pd.DataFrame:
        """Get historical EOD data - alias for get_aggregates with daily timespan."""
        return await self.get_aggregates(symbol, 1, timespan, start_date, end_date, limit=limit)
    
    async def get_forex_historical(self, symbol: str, start_date: str = None, end_date: str = None, 
                                  timespan: str = "day", limit: int = 365) -> pd.DataFrame:
        """Get historical forex data."""
        return await self.get_aggregates(symbol, 1, timespan, start_date, end_date, 'forex', limit)
    
    async def get_intraday_data(self, symbol: str, interval: str = "1min", 
                              start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get intraday data using aggregates endpoint."""
        # Map common intervals to Polygon timespan
        interval_map = {
            "1min": "minute",
            "5min": "minute", 
            "15min": "minute",
            "30min": "minute",
            "60min": "hour",
            "1h": "hour",
            "1d": "day"
        }
        
        multiplier_map = {
            "1min": 1,
            "5min": 5,
            "15min": 15, 
            "30min": 30,
            "60min": 1,
            "1h": 1,
            "1d": 1
        }
        
        timespan = interval_map.get(interval, "minute")
        multiplier = multiplier_map.get(interval, 1)
        
        # Default to today's data for intraday
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = end_date  # Same day for intraday
        
        return await self.get_aggregates(symbol, multiplier, timespan, start_date, end_date, limit=50000)
    
    async def list_tickers(self, market: str = "stocks", active: bool = True, limit: int = 1000) -> Dict[str, Any]:
        """List tickers - RATE LIMITED in free tier, use sparingly."""
        await self._rate_limit_check()
        
        try:
            tickers = self.client.list_tickers(
                market=market,
                active=active,
                limit=min(limit, 100)  # Limit to avoid rate limits
            )
            
            if tickers:
                return {
                    'success': True,
                    'tickers': [{'ticker': t.ticker, 'name': getattr(t, 'name', '')} for t in tickers],
                    'count': len(tickers)
                }
            else:
                return {'success': False, 'error': 'No tickers found'}
                
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                logger.warning(f"Rate limited on list_tickers: {e}")
                return {'success': False, 'error': 'Rate limited - free tier allows only 5 requests/minute'}
            else:
                logger.error(f"List tickers failed: {e}")
                return {'success': False, 'error': str(e)}
    
    async def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """Get ticker details - RATE LIMITED in free tier."""
        await self._rate_limit_check()
        
        try:
            details = self.client.get_ticker_details(symbol)
            
            if details:
                return {
                    'success': True,
                    'symbol': symbol,
                    'name': getattr(details, 'name', ''),
                    'description': getattr(details, 'description', ''),
                    'market': getattr(details, 'market', ''),
                    'locale': getattr(details, 'locale', ''),
                    'currency': getattr(details, 'currency_name', ''),
                    'type': getattr(details, 'type', '')
                }
            else:
                return {'success': False, 'error': f'No details found for {symbol}'}
                
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                logger.warning(f"Rate limited on ticker_details: {e}")
                return {'success': False, 'error': 'Rate limited - free tier allows only 5 requests/minute'}
            else:
                logger.error(f"Get ticker details failed for {symbol}: {e}")
                return {'success': False, 'error': str(e)}
    
    async def get_ticker_types(self) -> Dict[str, Any]:
        """Get ticker types - RATE LIMITED in free tier."""
        await self._rate_limit_check()
        
        try:
            types = self.client.get_ticker_types()
            
            if types:
                return {
                    'success': True,
                    'types': [{'code': t.code, 'description': getattr(t, 'description', '')} for t in types],
                    'count': len(types)
                }
            else:
                return {'success': False, 'error': 'No ticker types found'}
                
        except Exception as e:
            if "rate limit" in str(e).lower() or "429" in str(e):
                logger.warning(f"Rate limited on ticker_types: {e}")
                return {'success': False, 'error': 'Rate limited - free tier allows only 5 requests/minute'}
            else:
                logger.error(f"Get ticker types failed: {e}")
                return {'success': False, 'error': str(e)}
    
    async def get_related_companies(self, symbol: str) -> Dict[str, Any]:
        """Get related companies - NOT AVAILABLE in free tier."""
        return {
            'success': False, 
            'error': 'Related companies not available in free tier',
            'upgrade_message': 'Please upgrade your plan at https://polygon.io/pricing'
        }
    
    def format_symbol_for_display(self, symbol: str) -> str:
        """Format symbol for display (e.g., EURUSD -> EUR/USD)."""
        if len(symbol) == 6:
            return f"{symbol[:3]}/{symbol[3:]}"
        return symbol
    
    def get_major_pairs(self) -> List[str]:
        """Get list of major forex pairs."""
        return [
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
            "AUD/USD", "USD/CAD", "NZD/USD", "EUR/GBP",
            "EUR/JPY", "GBP/JPY", "CHF/JPY", "AUD/JPY",
            "EUR/CHF", "GBP/CHF", "AUD/CHF", "NZD/CHF"
        ]
