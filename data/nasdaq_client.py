"""
NASDAQ Data Link API Client
Provides access to NASDAQ's comprehensive financial and economic datasets
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pandas as pd
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class NASDAQDataset:
    """Represents a NASDAQ dataset"""
    database_code: str
    dataset_code: str
    name: str
    description: str
    frequency: str
    newest_available_date: Optional[str] = None
    oldest_available_date: Optional[str] = None

class NASDAQClient:
    """
    NASDAQ Data Link API Client
    
    Provides access to:
    - Stock prices and fundamentals
    - Economic indicators
    - Commodity prices
    - Currency exchange rates
    - Alternative datasets
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize NASDAQ client
        
        Args:
            api_key: NASDAQ API key (if not provided, will try to get from environment)
        """
        self.api_key = api_key or os.getenv('NASDAQ_API_KEY')
        if not self.api_key:
            raise ValueError("NASDAQ API key is required. Set NASDAQ_API_KEY environment variable.")
        
        self.base_url = "https://data.nasdaq.com/api/v3"
        self.session = None
        
        # Rate limiting
        self.rate_limit = 300  # requests per 10 minutes for premium
        self.request_times = []
        
        # Free database codes available with basic NASDAQ account
        self.databases = {
            'CFTC': 'Commodity Futures Trading Commission',
            'JODI': 'Joint Organisations Data Initiative',
            'ODA': 'IMF Cross Country Macroeconomic Statistics',
            'OPEC': 'OPEC Crude Oil Price',
            'WB': 'World Bank Global Economic Monitor',
            'WASDE': 'World Agricultural Supply and Demand Estimates'
        }
        
        # Premium databases (require paid subscription)
        self.premium_databases = {
            'WIKI': 'Wiki EOD Stock Prices',
            'EOD': 'End of Day US Stock Prices',
            'FRED': 'Federal Reserve Economic Data',
            'LBMA': 'London Bullion Market Association',
            'CHRIS': 'Continuous Futures',
            'CURRFX': 'Currency Exchange Rates',
            'RATEINF': 'Rate Information',
            'URC': 'Unicorn Research Corporation',
            'ZACKS': 'Zacks Fundamentals Collection A',
            'SF1': 'Core US Fundamentals Data',
            'SFP': 'S&P 500 Stock Prices',
            'MULTPL': 'Stock Market Indicators',
            'YALE': 'Yale Department of Economics',
            'ECONOMIST': 'The Economist'
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _check_rate_limit(self):
        """Check and enforce rate limiting"""
        now = time.time()
        # Remove requests older than 10 minutes
        self.request_times = [t for t in self.request_times if now - t < 600]
        
        if len(self.request_times) >= self.rate_limit:
            sleep_time = 600 - (now - self.request_times[0])
            if sleep_time > 0:
                logger.warning(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.request_times.append(now)
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with error handling and anti-bot measures"""
        self._check_rate_limit()
        
        if not self.session:
            # Create session with realistic headers to avoid bot detection
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification if needed
            self.session = aiohttp.ClientSession(headers=headers, connector=connector)
        
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to params
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        # Add small delay to avoid rapid requests
        await asyncio.sleep(0.5)
        
        try:
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:
                    logger.warning("Rate limit exceeded, waiting...")
                    await asyncio.sleep(60)
                    return await self._make_request(endpoint, params)
                elif response.status == 403:
                    logger.warning(f"Access forbidden (403) for {url}. This may be due to:")
                    logger.warning("- Invalid API key or insufficient permissions")
                    logger.warning("- IP-based restrictions or bot detection")
                    logger.warning("- Dataset requires premium subscription")
                    # Don't retry 403 errors, return empty result
                    return {"error": f"Access forbidden (403): {endpoint}"}
                elif response.status == 404:
                    logger.warning(f"Dataset not found (404): {endpoint}")
                    return {"error": f"Dataset not found (404): {endpoint}"}
                else:
                    error_text = await response.text()
                    logger.error(f"NASDAQ API error {response.status}: {error_text[:200]}...")  # Truncate long error messages
                    return {"error": f"NASDAQ API error {response.status}"}
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout error for NASDAQ API request: {endpoint}")
            return {"error": "Request timeout"}
        except Exception as e:
            logger.error(f"Error making NASDAQ API request: {e}")
            return {"error": str(e)}
    
    # Core API Methods
    
    async def get_dataset(self, database_code: str, dataset_code: str, 
                         start_date: Optional[str] = None, end_date: Optional[str] = None,
                         limit: Optional[int] = None, order: str = 'asc') -> pd.DataFrame:
        """
        Get dataset from NASDAQ
        
        Args:
            database_code: Database code (e.g., 'WIKI', 'EOD', 'FRED')
            dataset_code: Dataset code (e.g., 'AAPL', 'GDP')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            limit: Maximum number of rows
            order: Sort order ('asc' or 'desc')
        
        Returns:
            DataFrame with the dataset
        """
        endpoint = f"datasets/{database_code}/{dataset_code}/data"
        
        params = {'order': order}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if limit:
            params['limit'] = limit
        
        data = await self._make_request(endpoint, params)
        
        # Check for errors
        if 'error' in data:
            logger.warning(f"Error getting dataset {database_code}/{dataset_code}: {data['error']}")
            return pd.DataFrame()
        
        if 'dataset_data' in data:
            dataset_data = data['dataset_data']
            columns = dataset_data.get('column_names', [])
            rows = dataset_data.get('data', [])
            
            if not rows:
                logger.warning(f"No data rows found for {database_code}/{dataset_code}")
                return pd.DataFrame()
            
            df = pd.DataFrame(rows, columns=columns)
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            
            return df
        else:
            logger.warning(f"No dataset_data found for {database_code}/{dataset_code}")
            return pd.DataFrame()
    
    async def get_dataset_metadata(self, database_code: str, dataset_code: str) -> Dict[str, Any]:
        """Get metadata for a specific dataset"""
        endpoint = f"datasets/{database_code}/{dataset_code}/metadata"
        
        data = await self._make_request(endpoint)
        
        if 'error' in data:
            logger.warning(f"Error getting metadata for {database_code}/{dataset_code}: {data['error']}")
            return {}
        
        return data.get('dataset', {})
    
    async def search_datasets(self, query: str, database_code: Optional[str] = None,
                            per_page: int = 50) -> List[Dict[str, Any]]:
        """Search for datasets"""
        endpoint = "datasets"
        
        params = {
            'query': query,
            'per_page': per_page
        }
        if database_code:
            params['database_code'] = database_code
        
        data = await self._make_request(endpoint, params)
        
        if 'error' in data:
            logger.warning(f"Error searching datasets: {data['error']}")
            return []
        
        return data.get('datasets', [])
    
    async def get_databases(self) -> List[Dict[str, Any]]:
        """Get list of available databases"""
        endpoint = "databases"
        
        data = await self._make_request(endpoint)
        
        if 'error' in data:
            logger.warning(f"Error getting databases: {data['error']}")
            return []
        
        return data.get('databases', [])
    
    # Stock Market Data Methods
    
    async def get_stock_prices(self, symbol: str, start_date: Optional[str] = None,
                              end_date: Optional[str] = None, database: str = 'ODA') -> pd.DataFrame:
        """
        Get stock price data (limited with free account)
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            start_date: Start date
            end_date: End date
            database: Database to use (default: 'ODA' - only free option)
        
        Returns:
            DataFrame with stock prices
        
        Note:
            Stock price data requires premium subscription. Free account only has access to:
            CFTC, JODI, ODA, OPEC, WB, WASDE databases
        """
        if database not in self.databases:
            logger.warning(f"Database {database} not available with free account. Using ODA instead.")
            logger.info(f"Available free databases: {list(self.databases.keys())}")
            database = 'ODA'
        
        return await self.get_dataset(database, symbol, start_date, end_date)
    
    async def get_fundamentals(self, symbol: str, indicator: str = 'REVENUE',
                              start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get fundamental data for a stock
        
        Args:
            symbol: Stock symbol
            indicator: Fundamental indicator (REVENUE, NETINC, ASSETS, etc.)
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with fundamental data
        """
        dataset_code = f"{symbol}_{indicator}"
        return await self.get_dataset('SF1', dataset_code, start_date, end_date)
    
    async def get_market_indicators(self, indicator: str, start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get market indicators
        
        Args:
            indicator: Market indicator code
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with market indicator data
        """
        return await self.get_dataset('MULTPL', indicator, start_date, end_date)
    
    # Economic Data Methods
    
    async def get_economic_indicator(self, indicator: str, start_date: Optional[str] = None,
                                   end_date: Optional[str] = None, database: str = 'ODA') -> pd.DataFrame:
        """
        Get economic indicator data from free databases
        
        Args:
            indicator: Economic indicator code
            start_date: Start date
            end_date: End date
            database: Database to use (default: 'ODA' for IMF data, or 'WB' for World Bank)
        
        Returns:
            DataFrame with economic data
        """
        # Use free databases for economic data
        if database not in self.databases:
            logger.warning(f"Database {database} not available with free account. Trying free alternatives.")
            # Try ODA (IMF) first, then WB
            for free_db in ['ODA', 'WB']:
                df = await self.get_dataset(free_db, indicator, start_date, end_date)
                if not df.empty:
                    return df
            return pd.DataFrame()
        
        return await self.get_dataset(database, indicator, start_date, end_date)
    
    async def get_treasury_rates(self, maturity: str = '10Y', start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get US Treasury rates from free databases
        
        Args:
            maturity: Treasury maturity ('1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y')
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with treasury rates
        
        Note:
            Treasury rate data may be limited with free account. 
            Try ODA (IMF) or WB (World Bank) databases for interest rate data.
        """
        # Try to find treasury rate equivalents in free databases
        rate_codes = {
            '10Y': 'IRLTLT01',  # Long-term interest rates
            '3M': 'IRSTCI01',   # Short-term interest rates
            '1Y': 'IRSTCI01'
        }
        
        code = rate_codes.get(maturity, 'IRLTLT01')
        
        # Try ODA first (IMF data), then WB
        for db in ['ODA', 'WB']:
            df = await self.get_dataset(db, code, start_date, end_date)
            if not df.empty:
                return df
        
        logger.warning(f"Treasury rate data for {maturity} not available in free databases")
        return pd.DataFrame()
    
    # Commodity and Currency Methods
    
    async def get_commodity_prices(self, commodity: str, start_date: Optional[str] = None,
                                  end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get commodity prices using only free NASDAQ databases
        
        Args:
            commodity: Commodity code
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with commodity prices
        """
        # Commodity symbol mapping for FREE databases only
        commodity_mappings = {
            'OPEC': {
                'CRUDE_OIL_WTI': 'ORB',
                'CRUDE_OIL_BRENT': 'ORB',
                'CRUDE_OIL': 'ORB'
            },
            'CFTC': {
                # CFTC Commitments of Traders data
                'CRUDE_OIL_WTI': 'CRUDE_OIL_WTI_ALL',
                'NATURAL_GAS': 'NATURAL_GAS_ALL',
                'GOLD': 'GOLD_ALL',
                'SILVER': 'SILVER_ALL',
                'COPPER': 'COPPER_ALL',
                'WHEAT': 'WHEAT_ALL',
                'CORN': 'CORN_ALL',
                'SOYBEANS': 'SOYBEANS_ALL'
            },
            'JODI': {
                # Joint Organisations Data Initiative - oil data
                'CRUDE_OIL': 'WORLD_PRODUCTION',
                'CRUDE_OIL_WTI': 'WORLD_PRODUCTION',
                'CRUDE_OIL_BRENT': 'WORLD_PRODUCTION'
            },
            'WASDE': {
                # World Agricultural Supply and Demand Estimates
                'WHEAT': 'WHEAT_WORLD_PRODUCTION',
                'CORN': 'CORN_WORLD_PRODUCTION',
                'SOYBEANS': 'SOYBEANS_WORLD_PRODUCTION',
                'RICE': 'RICE_WORLD_PRODUCTION'
            }
        }
        
        # Try only FREE databases
        free_databases = ['OPEC', 'CFTC', 'JODI', 'WASDE']
        
        for db in free_databases:
            if db in commodity_mappings and commodity in commodity_mappings[db]:
                mapped_symbol = commodity_mappings[db][commodity]
                logger.info(f"Trying FREE {db} database with symbol {mapped_symbol} for {commodity}")
                
                df = await self.get_dataset(db, mapped_symbol, start_date, end_date)
                if not df.empty:
                    logger.info(f"Successfully retrieved {commodity} data from FREE {db} database")
                    return df
            else:
                # Try with original symbol as fallback
                logger.info(f"Trying FREE {db} database with original symbol {commodity}")
                df = await self.get_dataset(db, commodity, start_date, end_date)
                if not df.empty:
                    logger.info(f"Successfully retrieved {commodity} data from FREE {db} database")
                    return df
        
        logger.warning(f"No commodity data found for {commodity} in any FREE NASDAQ database")
        logger.info("Available free databases: CFTC, JODI, ODA, OPEC, WB, WASDE")
        return pd.DataFrame()
    
    async def get_currency_rates(self, currency_pair: str, start_date: Optional[str] = None,
                                end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get currency exchange rates from free databases
        
        Args:
            currency_pair: Currency pair (e.g., 'EURUSD', 'GBPUSD')
            start_date: Start date
            end_date: End date
        
        Returns:
            DataFrame with currency rates
        
        Note:
            Currency data requires premium subscription. Free account has limited access.
            Try ODA (IMF) database for some exchange rate data.
        """
        logger.warning("Currency exchange rate data requires premium subscription")
        logger.info("Trying ODA (IMF) database for limited exchange rate data")
        
        # Try ODA database for exchange rate data
        df = await self.get_dataset('ODA', currency_pair, start_date, end_date)
        if df.empty:
            logger.warning(f"No currency data found for {currency_pair} in free databases")
            logger.info("Consider using other data sources for currency rates")
        
        return df
    
    # High-level Analysis Methods
    
    async def get_sp500_data(self, start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> pd.DataFrame:
        """Get S&P 500 index data"""
        return await self.get_dataset('MULTPL', 'SP500_REAL_PRICE_MONTH', start_date, end_date)
    
    async def get_vix_data(self, start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> pd.DataFrame:
        """Get VIX volatility index data"""
        return await self.get_dataset('CHRIS', 'CBOE_VX1', start_date, end_date)
    
    async def get_yield_curve(self, date: Optional[str] = None) -> pd.DataFrame:
        """
        Get US Treasury yield curve
        
        Args:
            date: Specific date (YYYY-MM-DD), if None uses latest
        
        Returns:
            DataFrame with yield curve data
        """
        maturities = ['3M', '6M', '1Y', '2Y', '5Y', '10Y', '30Y']
        
        tasks = []
        for maturity in maturities:
            task = self.get_treasury_rates(maturity, date, date)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        yield_data = {}
        for i, result in enumerate(results):
            if isinstance(result, pd.DataFrame) and not result.empty:
                maturity = maturities[i]
                yield_data[maturity] = result.iloc[-1, 0] if len(result) > 0 else None
        
        return pd.DataFrame([yield_data])
    
    async def get_economic_dashboard(self, start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Get key economic indicators dashboard
        
        Returns:
            Dictionary with key economic datasets
        """
        indicators = {
            'GDP': 'GDP',
            'Unemployment': 'UNRATE',
            'Inflation': 'CPIAUCSL',
            'Fed_Rate': 'FEDFUNDS',
            'Consumer_Confidence': 'UMCSENT',
            'Industrial_Production': 'INDPRO',
            'Retail_Sales': 'RSAFS',
            'Housing_Starts': 'HOUST'
        }
        
        tasks = []
        for name, code in indicators.items():
            task = self.get_economic_indicator(code, start_date, end_date)
            tasks.append((name, task))
        
        results = {}
        for name, task in tasks:
            try:
                df = await task
                results[name] = df
            except Exception as e:
                logger.error(f"Error getting {name}: {e}")
                results[name] = pd.DataFrame()
        
        return results
    
    # Utility Methods
    
    def get_popular_datasets(self) -> Dict[str, List[str]]:
        """Get list of popular dataset codes by category"""
        return {
            'stocks': ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA'],
            'indices': ['SP500_REAL_PRICE_MONTH', 'NASDAQCOM', 'DJI'],
            'economic': ['GDP', 'UNRATE', 'CPIAUCSL', 'FEDFUNDS', 'DGS10'],
            'commodities': ['GOLD', 'SILVER', 'CRUDE_OIL', 'NATURAL_GAS'],
            'currencies': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD'],
            'crypto': ['BTCUSD', 'ETHUSD', 'ADAUSD']
        }
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()

# Convenience functions for synchronous usage
def create_nasdaq_client() -> NASDAQClient:
    """Create a NASDAQ client instance"""
    return NASDAQClient()

async def get_stock_data(symbol: str, days: int = 365) -> pd.DataFrame:
    """Quick function to get stock data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    async with NASDAQClient() as client:
        return await client.get_stock_prices(
            symbol, 
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

async def get_economic_data(indicator: str, days: int = 365) -> pd.DataFrame:
    """Quick function to get economic data"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    async with NASDAQClient() as client:
        return await client.get_economic_indicator(
            indicator,
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
