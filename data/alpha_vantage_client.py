"""
Alpha Vantage API client for forex data as fallback.
Free tier provides good forex data access.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import json

logger = logging.getLogger(__name__)


class AlphaVantageClient:
    """Client for Alpha Vantage API as forex data fallback."""
    
    def __init__(self, api_key: str = "demo"):
        """Initialize Alpha Vantage client."""
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.session = None
        
        # Rate limiting (Free tier: 25 requests per day, 5 per minute)
        self.rate_limit = 5  # requests per minute
        self.rate_window = 60  # seconds
        self.request_times = []
        
    async def initialize(self):
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession()
        
    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
    
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get quote data for a symbol."""
        if not self.session:
            await self.initialize()
        
        await self._rate_limit_check()
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.request_times.append(time.time())
                    
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        return {
                            'symbol': symbol,
                            'price': float(quote.get("05. price", 0)),
                            'change': float(quote.get("09. change", 0)),
                            'change_percent': quote.get("10. change percent", "0%").replace("%", ""),
                            'volume': int(quote.get("06. volume", 0)),
                            'timestamp': quote.get("07. latest trading day"),
                            'source': 'Alpha Vantage'
                        }
                    else:
                        return {'error': 'No quote data found', 'symbol': symbol}
                else:
                    return {'error': f'HTTP {response.status}', 'symbol': symbol}
        except Exception as e:
            logger.error(f"Alpha Vantage quote error for {symbol}: {e}")
            return {'error': str(e), 'symbol': symbol}
    
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
    
    async def _make_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make rate-limited API request."""
        await self._rate_limit_check()
        
        if not self.session:
            await self.initialize()
        
        params['apikey'] = self.api_key
        
        try:
            async with self.session.get(self.base_url, params=params) as response:
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
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    return {"error": f"API request failed: {response.status}"}
                    
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"error": str(e)}
    
    async def get_forex_quote(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get real-time forex quote with caching."""
        import json
        import os
        
        cache_file = f"cache/{symbol.replace('/', '')}_quote_alphavantage.json"
        cache_duration = 300  # 5 minutes
        
        # Check cache first (unless force refresh)
        if not force_refresh and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached forex quote for {symbol} (age: {cache_age:.1f}s)")
                        return cached_data
            except Exception as e:
                logger.warning(f"Cache read error for {symbol}: {e}")
        
        # Format symbol for Alpha Vantage (e.g., EUR/USD -> EURUSD)
        from_currency, to_currency = symbol.replace('/', '').upper()[:3], symbol.replace('/', '').upper()[3:]
        
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency
        }
        
        result = await self._make_request(params)
        
        # Add timestamp and cache the result
        if 'error' not in result:
            result['timestamp'] = time.time()
            try:
                os.makedirs('cache', exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
                logger.info(f"Cached fresh forex quote for {symbol}")
            except Exception as e:
                logger.warning(f"Cache write error for {symbol}: {e}")
        
        return result
    
    async def get_forex_daily(self, symbol: str, outputsize: str = "compact", use_cache: bool = True) -> Dict[str, Any]:
        """Get daily forex data with incremental caching."""
        import json
        import os
        
        cache_file = f"cache/{symbol.replace('/', '')}_daily_alphavantage.json"
        cache_duration = 3600  # 1 hour for daily data
        
        # Try incremental update if cache exists
        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    logger.info(f"Using cached daily forex data for {symbol} (age: {cache_age:.1f}s)")
                    return cached_data
                
                # For daily data, we can check if we have recent data and only fetch if needed
                time_series = cached_data.get("Time Series (Daily)", {})
                if time_series:
                    latest_date_str = max(time_series.keys())
                    latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
                    days_old = (datetime.now() - latest_date).days
                    
                    # If cache is less than 2 days old, use it (markets closed on weekends)
                    if days_old < 2:
                        logger.info(f"Using recent cached daily data for {symbol} ({days_old} days old)")
                        return cached_data
                        
            except Exception as e:
                logger.warning(f"Daily cache error for {symbol}: {e}")
        
        # Format symbol for Alpha Vantage
        from_currency, to_currency = symbol.replace('/', '').upper()[:3], symbol.replace('/', '').upper()[3:]
        
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": outputsize  # compact = last 100 days, full = 20+ years
        }
        
        result = await self._make_request(params)
        
        # Cache the result
        if use_cache and 'error' not in result:
            try:
                os.makedirs('cache', exist_ok=True)
                result['timestamp'] = time.time()
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
                logger.info(f"Cached daily forex data for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to cache daily data for {symbol}: {e}")
        
        return result
    
    async def get_forex_intraday(self, symbol: str, interval: str = "60min", use_cache: bool = True) -> Dict[str, Any]:
        """Get intraday forex data with caching."""
        import json
        import os
        
        cache_file = f"cache/{symbol.replace('/', '')}_intraday_{interval}_alphavantage.json"
        cache_duration = 1800  # 30 minutes for intraday data
        
        # Check cache first
        if use_cache and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached intraday data for {symbol} (age: {cache_age:.1f}s)")
                        return cached_data
            except Exception as e:
                logger.warning(f"Intraday cache error for {symbol}: {e}")
        
        from_currency, to_currency = symbol.replace('/', '').upper()[:3], symbol.replace('/', '').upper()[3:]
        
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "interval": interval
        }
        
        result = await self._make_request(params)
        
        # Cache the result
        if use_cache and 'error' not in result:
            try:
                os.makedirs('cache', exist_ok=True)
                result['timestamp'] = time.time()
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
                logger.info(f"Cached intraday data for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to cache intraday data for {symbol}: {e}")
        
        return result
    
    async def get_comprehensive_forex_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive forex analysis data using Alpha Vantage."""
        try:
            logger.info(f"Fetching forex data from Alpha Vantage for {symbol}")
            
            # Get current quote
            quote_data = await self.get_forex_quote(symbol)
            
            # Get daily historical data
            daily_data = await self.get_forex_daily(symbol, "compact")  # Last 100 days
            
            # Get intraday data
            intraday_data = await self.get_forex_intraday(symbol, "60min")
            
            # Process the data into a consistent format
            processed_data = {
                "symbol": symbol,
                "quote": self._process_quote_data(quote_data),
                "daily_data": self._process_daily_data(daily_data),
                "hourly_data": self._process_intraday_data(intraday_data),
                "market_status": {"currencies": {"fx": "open"}},  # Alpha Vantage doesn't provide market status
                "news": [],  # Alpha Vantage doesn't provide news in free tier
                "timestamp": datetime.now().isoformat(),
                "source": "Alpha Vantage"
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error in Alpha Vantage forex analysis: {e}")
            return {"error": str(e)}
    
    def _process_quote_data(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process quote data into consistent format."""
        if "error" in quote_data:
            return {}
        
        exchange_rate = quote_data.get("Realtime Currency Exchange Rate", {})
        if not exchange_rate:
            return {}
        
        return {
            "price": float(exchange_rate.get("5. Exchange Rate", 0)),
            "timestamp": exchange_rate.get("6. Last Refreshed", ""),
            "from_currency": exchange_rate.get("1. From_Currency Code", ""),
            "to_currency": exchange_rate.get("3. To_Currency Code", "")
        }
    
    def _process_daily_data(self, daily_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process daily data into consistent format."""
        if "error" in daily_data:
            return []
        
        time_series = daily_data.get("Time Series (Daily)", {})
        if not time_series:
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
                    "v": 0  # Alpha Vantage doesn't provide volume for forex
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Error processing daily data for {date_str}: {e}")
                continue
        
        # Sort by timestamp descending (most recent first)
        return sorted(processed, key=lambda x: x["t"], reverse=True)
    
    def _process_intraday_data(self, intraday_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process intraday data into consistent format."""
        if "error" in intraday_data:
            return []
        
        # Find the time series key (it varies by interval)
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
                    "v": 0  # Alpha Vantage doesn't provide volume for forex
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Error processing intraday data for {datetime_str}: {e}")
                continue
        
        # Sort by timestamp descending and limit to last 24 hours
        processed = sorted(processed, key=lambda x: x["t"], reverse=True)
        return processed[:24]  # Last 24 hours
    
    def get_major_pairs(self) -> List[str]:
        """Get list of major forex pairs supported by Alpha Vantage."""
        return [
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
            "AUD/USD", "USD/CAD", "NZD/USD", "EUR/GBP",
            "EUR/JPY", "GBP/JPY", "CHF/JPY", "AUD/JPY",
            "EUR/CHF", "GBP/CHF", "AUD/CHF", "NZD/CHF"
        ]
        
    async def get_historical_data(self, symbol: str, interval: str = "daily", outputsize: str = "compact", use_cache: bool = True) -> Dict[str, Any]:
        """Get historical stock data with caching.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'ANZ.AX')
            interval: Data interval ('daily', '60min', etc.)
            outputsize: 'compact' (100 data points) or 'full' (20+ years)
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary with historical data or error
        """
        import json
        import os
        import pandas as pd
        
        # Handle special symbols
        clean_symbol = symbol
        if '.' in symbol:
            # For exchange-specific symbols like ANZ.AX
            clean_symbol = symbol
        
        cache_file = f"cache/stock_{clean_symbol}_{interval}_alphavantage.json"
        cache_duration = 3600  # 1 hour for stock data
        
        # Check cache first
        if use_cache and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached stock data for {symbol} (age: {cache_age:.1f}s)")
                        return cached_data
            except Exception as e:
                logger.warning(f"Stock cache error for {symbol}: {e}")
        
        # Determine function based on interval
        if interval == "daily":
            function = "TIME_SERIES_DAILY"
            time_series_key = "Time Series (Daily)"
        elif interval == "weekly":
            function = "TIME_SERIES_WEEKLY"
            time_series_key = "Weekly Time Series"
        elif interval == "monthly":
            function = "TIME_SERIES_MONTHLY"
            time_series_key = "Monthly Time Series"
        elif "min" in interval:
            function = "TIME_SERIES_INTRADAY"
            time_series_key = f"Time Series ({interval})"
        else:
            function = "TIME_SERIES_DAILY"
            time_series_key = "Time Series (Daily)"
        
        params = {
            "function": function,
            "symbol": clean_symbol,
            "outputsize": outputsize
        }
        
        # Add interval parameter for intraday data
        if function == "TIME_SERIES_INTRADAY":
            params["interval"] = interval
        
        result = await self._make_request(params)
        
        # Cache the result
        if use_cache and 'error' not in result:
            try:
                os.makedirs('cache', exist_ok=True)
                result['timestamp'] = time.time()
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
                logger.info(f"Cached stock data for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to cache stock data for {symbol}: {e}")
        
        # Convert to pandas DataFrame format
        if 'error' not in result and time_series_key in result:
            try:
                time_series = result[time_series_key]
                data = []
                
                for date_str, values in time_series.items():
                    data_point = {
                        'date': date_str,
                        'open': float(values.get('1. open', 0)),
                        'high': float(values.get('2. high', 0)),
                        'low': float(values.get('3. low', 0)),
                        'close': float(values.get('4. close', 0)),
                        'volume': int(float(values.get('5. volume', 0)))
                    }
                    data.append(data_point)
                
                # Sort by date (newest first)
                data = sorted(data, key=lambda x: x['date'], reverse=True)
                
                # Create DataFrame
                df = pd.DataFrame(data)
                
                # Add to result
                result['dataframe'] = df.to_dict('records')
            except Exception as e:
                logger.error(f"Error processing stock data for {symbol}: {e}")
        
        return result
