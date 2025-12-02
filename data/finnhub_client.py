"""Finnhub API client using official Python SDK.

FREE TIER CAPABILITIES (66.7% success rate):
✅ Real-time quotes, company profiles, news, financials, earnings, recommendations
❌ Historical candles, price targets, forex rates, economic calendar
"""

import asyncio
import logging
import time
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import finnhub

logger = logging.getLogger(__name__)


class FinnhubClient:
    """Client for Finnhub API using official Python SDK.
    
    FREE TIER STRENGTHS:
    - Real-time quotes ✅
    - Company profiles ✅ 
    - Company news ✅
    - Basic financials ✅
    - Earnings data ✅
    - Analyst recommendations ✅
    - Stock symbols ✅
    - Market status ✅
    - General news ✅
    """
    
    def __init__(self, api_key: str):
        """Initialize Finnhub client with official SDK."""
        self.api_key = api_key
        self.client = finnhub.Client(api_key=api_key)
        
        # Rate limiting for free tier
        self.rate_limit = 60  # requests per minute (more generous than Polygon)
        self.rate_window = 60  # seconds
        self.request_times = []
        
        # Ensure cache directory exists
        os.makedirs('cache', exist_ok=True)
        
        logger.info("Finnhub Free Tier: Strong real-time data, limited historical data")
    
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
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile information using official SDK."""
        try:
            profile = self.client.company_profile2(symbol=symbol)
            
            if profile:
                return {
                    'symbol': symbol,
                    'name': profile.get('name', ''),
                    'country': profile.get('country', ''),
                    'currency': profile.get('currency', ''),
                    'exchange': profile.get('exchange', ''),
                    'industry': profile.get('finnhubIndustry', ''),
                    'ipo': profile.get('ipo', ''),
                    'market_cap': profile.get('marketCapitalization', 0),
                    'outstanding_shares': profile.get('shareOutstanding', 0),
                    'website': profile.get('weburl', ''),
                    'logo': profile.get('logo', ''),
                    'source': 'Finnhub'
                }
            else:
                return {'error': f'No profile data found for {symbol}'}
            
        except Exception as e:
            logger.error(f"Error fetching company profile for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_general_news(self, category: str = 'general', limit: int = 10) -> List[Dict[str, Any]]:
        """Get general market news using official SDK - AVAILABLE in free tier."""
        try:
            # Use official SDK for general news
            news_data = self.client.general_news(category, min_id=0)
            
            if news_data:
                # Format and limit news items
                formatted_news = []
                for item in news_data[:limit]:
                    formatted_news.append({
                        'headline': item.get('headline', ''),
                        'summary': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'datetime': item.get('datetime', 0),
                        'source': item.get('source', ''),
                        'category': item.get('category', ''),
                        'image': item.get('image', '')
                    })
                
                return formatted_news
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error fetching general news: {e}")
            return []
    
    def get_quote(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get real-time quote using official SDK - AVAILABLE in free tier."""
        cache_file = f"cache/{symbol}_quote_finnhub.json"
        cache_duration = 300  # 5 minutes
        
        # Check cache first (unless force refresh)
        if not force_refresh and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached quote for {symbol} (age: {cache_age:.0f}s)")
                        return cached_data
            except Exception as e:
                logger.warning(f"Cache read error for {symbol}: {e}")
        
        try:
            # Use official SDK for quote
            data = self.client.quote(symbol)
            
            if data and data.get('c') is not None:
                # Format the response
                quote_data = {
                    'symbol': symbol,
                    'current_price': data.get('c', 0),
                    'change': data.get('d', 0),
                    'percent_change': data.get('dp', 0),
                    'high': data.get('h', 0),
                    'low': data.get('l', 0),
                    'open': data.get('o', 0),
                    'previous_close': data.get('pc', 0),
                    'timestamp': data.get('t', 0),
                    'source': 'Finnhub'
                }
                
                # Cache the result
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(quote_data, f)
                except Exception as e:
                    logger.warning(f"Cache write error for {symbol}: {e}")
                
                return quote_data
            else:
                return {'error': f'No quote data available for {symbol}'}
            
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_company_news(self, symbol: str, days_back: int = 7, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get company news using official SDK - AVAILABLE in free tier."""
        cache_file = f"cache/{symbol}_news_finnhub.json"
        cache_duration = 3600  # 1 hour for news
        
        # Check cache first
        if use_cache and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached news for {symbol} (age: {cache_age:.1f}s)")
                        return cached_data.get('articles', [])
            except Exception as e:
                logger.warning(f"News cache error for {symbol}: {e}")
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Use official SDK for company news
            news_data = self.client.company_news(symbol, 
                                                _from=start_date.strftime('%Y-%m-%d'),
                                                to=end_date.strftime('%Y-%m-%d'))
            
            if news_data:
                # Format news articles
                formatted_news = []
                for item in news_data:
                    formatted_news.append({
                        'headline': item.get('headline', ''),
                        'summary': item.get('summary', ''),
                        'url': item.get('url', ''),
                        'datetime': item.get('datetime', 0),
                        'source': item.get('source', ''),
                        'category': item.get('category', ''),
                        'image': item.get('image', ''),
                        'id': item.get('id', str(item.get('datetime', 0)))
                    })
                
                # Cache the result
                if use_cache:
                    try:
                        cache_data = {'articles': formatted_news, 'timestamp': time.time()}
                        with open(cache_file, 'w') as f:
                            json.dump(cache_data, f)
                    except Exception as e:
                        logger.warning(f"Failed to cache news for {symbol}: {e}")
                
                return formatted_news
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error fetching company news for {symbol}: {e}")
            return []
    
    def get_insider_transactions(self, symbol: str) -> List[Dict[str, Any]]:
        """Get insider transactions using official SDK - AVAILABLE in free tier."""
        try:
            # Use official SDK for insider transactions
            data = self.client.stock_insider_transactions(symbol)
            
            if data and data.get('data'):
                return data.get('data', [])
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error fetching insider transactions for {symbol}: {e}")
            return []
    
    def get_basic_financials(self, symbol: str) -> Dict[str, Any]:
        """Get basic financial metrics using official SDK - AVAILABLE in free tier."""
        try:
            # Use official SDK for basic financials
            data = self.client.company_basic_financials(symbol, 'all')
            
            if data and data.get('metric'):
                # Extract key metrics
                metrics = data.get('metric', {})
                
                return {
                    'symbol': symbol,
                    'pe_ratio': metrics.get('peBasicExclExtraTTM'),
                    'price_to_book': metrics.get('pbQuarterly'),
                    'price_to_sales': metrics.get('psQuarterly'),
                    'roe': metrics.get('roeRfy'),
                    'roa': metrics.get('roaRfy'),
                    'debt_to_equity': metrics.get('totalDebt/totalEquityQuarterly'),
                    'current_ratio': metrics.get('currentRatioQuarterly'),
                    'gross_margin': metrics.get('grossMarginTTM'),
                    'operating_margin': metrics.get('operatingMarginTTM'),
                    'net_margin': metrics.get('netProfitMarginTTM'),
                    'beta': metrics.get('beta'),
                    '52_week_high': metrics.get('52WeekHigh'),
                    '52_week_low': metrics.get('52WeekLow'),
                    'source': 'Finnhub'
                }
            else:
                return {'error': f'No financial data available for {symbol}'}
            
        except Exception as e:
            logger.error(f"Error fetching basic financials for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_recommendation_trends(self, symbol: str) -> List[Dict[str, Any]]:
        """Get analyst recommendation trends using official SDK - AVAILABLE in free tier."""
        try:
            # Use official SDK for recommendation trends
            data = self.client.recommendation_trends(symbol)
            
            if data:
                return data
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error fetching recommendations for {symbol}: {e}")
            return []
    
    def get_earnings(self, symbol: str) -> List[Dict[str, Any]]:
        """Get earnings data using official SDK - AVAILABLE in free tier."""
        try:
            # Use official SDK for earnings surprises (correct method name)
            data = self.client.company_earnings(symbol, limit=5)
            
            if data:
                return data
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error fetching earnings for {symbol}: {e}")
            return []
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """Get historical stock data - NOT AVAILABLE in free tier."""
        return {
            'error': 'Historical candle data not available in Finnhub free tier',
            'upgrade_message': 'Please upgrade your plan for historical data access',
            'symbol': symbol,
            'source': 'Finnhub',
            'alternative': 'Use Polygon for historical data or upgrade Finnhub plan'
        }
    
    def get_market_status(self) -> Dict[str, Any]:
        """Get market status using official SDK - AVAILABLE in free tier."""
        try:
            # Use official SDK for market status
            status = self.client.market_status(exchange='US')
            
            if status:
                return {
                    'exchange': 'US',
                    'is_open': status.get('isOpen', False),
                    'session': status.get('session', ''),
                    'timezone': status.get('timezone', ''),
                    'source': 'Finnhub'
                }
            else:
                return {'error': 'No market status data available'}
            
        except Exception as e:
            logger.error(f"Error fetching market status: {e}")
            return {'error': str(e)}
    
    def get_stock_symbols(self, exchange: str = 'US') -> List[Dict[str, Any]]:
        """Get stock symbols using official SDK - AVAILABLE in free tier."""
        try:
            # Use official SDK for stock symbols
            symbols = self.client.stock_symbols(exchange)
            
            if symbols:
                return symbols
            else:
                return []
            
        except Exception as e:
            logger.error(f"Error fetching stock symbols for {exchange}: {e}")
            return []
    
    def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive stock analysis data using all available free tier endpoints."""
        try:
            logger.info(f"Fetching comprehensive data for {symbol}...")
            
            # Add small delays between API calls to respect rate limits
            profile = self.get_company_profile(symbol)
            time.sleep(0.1)
            
            quote = self.get_quote(symbol)
            time.sleep(0.1)
            
            news = self.get_company_news(symbol, days_back=7)
            time.sleep(0.1)
            
            insider_transactions = self.get_insider_transactions(symbol)
            time.sleep(0.1)
            
            financials = self.get_basic_financials(symbol)
            time.sleep(0.1)
            
            recommendations = self.get_recommendation_trends(symbol)
            time.sleep(0.1)
            
            earnings = self.get_earnings(symbol)
            
            return {
                'symbol': symbol,
                'profile': profile,
                'quote': quote,
                'news': news,
                'insider_transactions': insider_transactions,
                'financials': financials,
                'recommendations': recommendations,
                'earnings': earnings,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
            return {'error': str(e)}
    
    # Methods NOT available in free tier
    def get_historical_candles(self, symbol: str, resolution: str = 'D', days_back: int = 30) -> Dict[str, Any]:
        """Historical candles - NOT AVAILABLE in free tier."""
        return {
            'error': 'Historical candle data not available in Finnhub free tier',
            'upgrade_message': 'Please upgrade your plan for historical data access',
            'symbol': symbol,
            'source': 'Finnhub',
            'alternative': 'Use Polygon for historical data or upgrade Finnhub plan'
        }
    
    def get_price_target(self, symbol: str) -> Dict[str, Any]:
        """Price targets - NOT AVAILABLE in free tier."""
        return {
            'error': 'Price target data not available in Finnhub free tier',
            'upgrade_message': 'Please upgrade your plan for price target access',
            'symbol': symbol,
            'source': 'Finnhub'
        }
    
    def get_forex_rates(self, base: str = 'USD', quote: str = 'EUR') -> Dict[str, Any]:
        """Forex rates - NOT AVAILABLE in free tier."""
        return {
            'error': 'Forex rates not available in Finnhub free tier',
            'upgrade_message': 'Please upgrade your plan for forex data access',
            'pair': f'{base}/{quote}',
            'source': 'Finnhub'
        }
    
    def get_economic_calendar(self) -> Dict[str, Any]:
        """Economic calendar - NOT AVAILABLE in free tier."""
        return {
            'error': 'Economic calendar not available in Finnhub free tier',
            'upgrade_message': 'Please upgrade your plan for economic calendar access',
            'source': 'Finnhub'
        }
