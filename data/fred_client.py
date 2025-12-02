"""
Federal Reserve Economic Data (FRED) API client.
Provides access to economic data from the St. Louis Federal Reserve.
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class FREDClient:
    """Client for Federal Reserve Economic Data (FRED) API."""
    
    def __init__(self, config: MarketResearcherConfig):
        """Initialize FRED client."""
        self.config = config
        self.fred_key = config.fred_api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self.session = None
        
        # Rate limiting: FRED allows 120 requests per 60 seconds
        self.request_times = []
        self.max_requests_per_minute = 120
        
        if not self.fred_key:
            logger.warning("FRED API key not found. Set FRED_API_KEY in your .env file.")
    
    async def initialize(self):
        """Initialize the HTTP session."""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _rate_limit_check(self):
        """Check and enforce rate limits."""
        now = datetime.now()
        
        # Remove requests older than 1 minute
        self.request_times = [
            req_time for req_time in self.request_times 
            if now - req_time < timedelta(minutes=1)
        ]
        
        # If we're at the limit, wait
        if len(self.request_times) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self.request_times.append(now)
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make request to FRED API."""
        await self._rate_limit_check()
        
        if not self.session:
            await self.initialize()
        
        if not self.fred_key:
            return {"error": "FRED API key not configured"}
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        params.update({
            'api_key': self.fred_key,
            'file_type': 'json'
        })
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for API error messages
                    if 'error_code' in data:
                        return {"error": f"FRED API error {data['error_code']}: {data.get('error_message', 'Unknown error')}"}
                    
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"FRED API request failed: {response.status} - {error_text}")
                    return {"error": f"API request failed: {response.status}"}
                    
        except Exception as e:
            logger.error(f"FRED request error: {e}")
            return {"error": str(e)}
    
    async def get_series(self, series_id: str, start_date: str = None, end_date: str = None, 
                        limit: int = None, offset: int = None) -> Dict[str, Any]:
        """Get observations for a FRED data series."""
        params = {'series_id': series_id}
        
        if start_date:
            params['observation_start'] = start_date
        if end_date:
            params['observation_end'] = end_date
        if limit:
            params['limit'] = limit
        if offset:
            params['offset'] = offset
        
        return await self._make_request('series/observations', params)
    
    async def get_series_info(self, series_id: str) -> Dict[str, Any]:
        """Get information about a FRED data series."""
        params = {'series_id': series_id}
        return await self._make_request('series', params)
    
    async def search_series(self, search_text: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Search for FRED data series."""
        params = {
            'search_text': search_text,
            'limit': limit,
            'offset': offset
        }
        return await self._make_request('series/search', params)
    
    async def get_categories(self, category_id: int = None) -> Dict[str, Any]:
        """Get FRED categories."""
        params = {}
        if category_id:
            params['category_id'] = category_id
        return await self._make_request('category', params)
    
    async def get_category_series(self, category_id: int, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get series in a specific category."""
        params = {
            'category_id': category_id,
            'limit': limit,
            'offset': offset
        }
        return await self._make_request('category/series', params)
    
    async def get_releases(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get FRED releases."""
        params = {
            'limit': limit,
            'offset': offset
        }
        return await self._make_request('releases', params)
    
    async def get_release_series(self, release_id: int, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """Get series for a specific release."""
        params = {
            'release_id': release_id,
            'limit': limit,
            'offset': offset
        }
        return await self._make_request('release/series', params)
    
    async def get_economic_indicators(self) -> Dict[str, Any]:
        """Get popular economic indicators."""
        indicators = {
            'GDP': 'GDP',
            'Unemployment Rate': 'UNRATE',
            'Inflation (CPI)': 'CPIAUCSL',
            'Federal Funds Rate': 'FEDFUNDS',
            'Consumer Sentiment': 'UMCSENT',
            'Industrial Production': 'INDPRO',
            'Housing Starts': 'HOUST',
            'Retail Sales': 'RSAFS',
            'Personal Income': 'PI',
            'Consumer Price Index': 'CPIAUCSL',
            'Producer Price Index': 'PPIACO',
            'Employment Cost Index': 'ECIALLCIV',
            'Real GDP': 'GDPC1',
            'M2 Money Supply': 'M2SL',
            'Treasury 10Y': 'GS10',
            'Treasury 2Y': 'GS2',
            'Corporate Bond Yield': 'BAA',
            'Dollar Index': 'DTWEXBGS'
        }
        
        results = {}
        for name, series_id in indicators.items():
            try:
                data = await self.get_series(series_id, limit=1)
                if 'observations' in data and data['observations']:
                    latest = data['observations'][-1]
                    results[name] = {
                        'series_id': series_id,
                        'value': latest.get('value', 'N/A'),
                        'date': latest.get('date', 'N/A')
                    }
            except Exception as e:
                logger.error(f"Error fetching {name} ({series_id}): {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    async def get_yield_curve_data(self) -> Dict[str, Any]:
        """Get current yield curve data."""
        yield_series = {
            '1M': 'GS1M',
            '3M': 'GS3M', 
            '6M': 'GS6M',
            '1Y': 'GS1',
            '2Y': 'GS2',
            '3Y': 'GS3',
            '5Y': 'GS5',
            '7Y': 'GS7',
            '10Y': 'GS10',
            '20Y': 'GS20',
            '30Y': 'GS30'
        }
        
        results = {}
        for maturity, series_id in yield_series.items():
            try:
                data = await self.get_series(series_id, limit=1)
                if 'observations' in data and data['observations']:
                    latest = data['observations'][-1]
                    results[maturity] = {
                        'rate': float(latest.get('value', 0)) if latest.get('value', '.') != '.' else None,
                        'date': latest.get('date', 'N/A')
                    }
            except Exception as e:
                logger.error(f"Error fetching {maturity} yield ({series_id}): {e}")
                results[maturity] = {'error': str(e)}
        
        return results
    
    async def get_inflation_data(self, months: int = 12) -> Dict[str, Any]:
        """Get recent inflation data."""
        series_ids = {
            'CPI All Items': 'CPIAUCSL',
            'CPI Core': 'CPILFESL', 
            'PCE': 'PCEPI',
            'PCE Core': 'PCEPILFE',
            'Producer Price Index': 'PPIACO'
        }
        
        results = {}
        for name, series_id in series_ids.items():
            try:
                data = await self.get_series(series_id, limit=months)
                if 'observations' in data and data['observations']:
                    observations = [obs for obs in data['observations'] if obs.get('value', '.') != '.']
                    if len(observations) >= 2:
                        latest = float(observations[-1]['value'])
                        year_ago = float(observations[-12]['value']) if len(observations) >= 12 else float(observations[0]['value'])
                        yoy_change = ((latest - year_ago) / year_ago) * 100
                        
                        results[name] = {
                            'series_id': series_id,
                            'current_value': latest,
                            'yoy_change': round(yoy_change, 2),
                            'date': observations[-1]['date']
                        }
            except Exception as e:
                logger.error(f"Error fetching {name} inflation data ({series_id}): {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    async def get_commodity_data(self) -> Dict[str, Any]:
        """Get current commodity price data from FRED."""
        commodity_series = {
            # Energy Commodities
            'WTI Crude Oil': 'DCOILWTICO',
            'Brent Crude Oil': 'DCOILBRENTEU', 
            'Natural Gas': 'DHHNGSP',
            'Heating Oil': 'DHOILNYH',
            'Gasoline': 'DGASNYH',
            'Propane': 'DPROPANEMBTX',
            
            # Precious Metals (corrected codes)
            'Gold': 'NASDAQQGLDI',
            'Silver': 'NASDAQQSLVO',
            'Palladium': 'PALLFNFINDEXM',
            
            # Industrial Metals
            'Copper': 'PCOPPUSDM',
            'Aluminum': 'PALUMUSDM',
            'Zinc': 'PZINCUSDM',
            'Nickel': 'PNICKUSDM',
            'Lead': 'PLEADUSDM',
            'Tin': 'PTINUSDM',
            
            # Agricultural Commodities
            'Wheat': 'PWHEAMTUSDM',
            'Corn': 'PMAIZMTUSDM',
            'Rice': 'PRICENPQUSDM',
            'Soybeans': 'PSOYBUSDM',
            'Sugar': 'PSUGAISAUSDM',
            'Coffee': 'PCOFFOTMUSDM',
            'Cotton': 'PCOTTINDUSDM',
            'Cocoa': 'PCOCOUSDM',
            
            # Livestock
            'Beef': 'PBEEFUSDM',
            'Pork': 'PPORKUSDM',
            'Poultry': 'PPOULTUSDM',
            'Fish': 'PSALMUSDM',
            
            # Other Commodities
            'Timber': 'WPS081',
            'Rubber': 'PRUBBUSDM',
            'Fertilizers': 'IR12510',
            'Coal': 'PCOALAUUSDM',
            'Iron Ore': 'PIORECRUSDM',
            
            # Commodity Indices
            'All Commodities Index': 'PALLFNFINDEXQ',
            'Food Index': 'PFOODINDEXQ',
            'Industrial Inputs Index': 'PINDUINDEXQ',
            'Agricultural Raw Materials Index': 'PRAWMINDEXQ',
            'Metals Index': 'PMETAINDEXQ'
        }
        
        results = {}
        for name, series_id in commodity_series.items():
            try:
                data = await self.get_series(series_id, limit=1)
                if 'observations' in data and data['observations']:
                    latest = data['observations'][-1]
                    if latest.get('value', '.') != '.':
                        results[name] = {
                            'series_id': series_id,
                            'value': float(latest['value']),
                            'date': latest.get('date', 'N/A')
                        }
                    else:
                        results[name] = {'error': 'No data available'}
                else:
                    results[name] = {'error': 'No observations found'}
            except Exception as e:
                logger.error(f"Error fetching {name} commodity data ({series_id}): {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    def get_popular_series(self) -> Dict[str, str]:
        """Get a dictionary of popular FRED series IDs and their descriptions."""
        return {
            # Economic Growth
            'GDP': 'Gross Domestic Product',
            'GDPC1': 'Real Gross Domestic Product',
            'GDPPOT': 'Real Potential Gross Domestic Product',
            
            # Employment
            'UNRATE': 'Unemployment Rate',
            'PAYEMS': 'All Employees, Total Nonfarm',
            'CIVPART': 'Labor Force Participation Rate',
            'EMRATIO': 'Employment-Population Ratio',
            
            # Inflation
            'CPIAUCSL': 'Consumer Price Index for All Urban Consumers: All Items',
            'CPILFESL': 'Consumer Price Index for All Urban Consumers: All Items Less Food and Energy',
            'PCEPI': 'Personal Consumption Expenditures: Chain-type Price Index',
            'PCEPILFE': 'Personal Consumption Expenditures Excluding Food and Energy',
            
            # Interest Rates
            'FEDFUNDS': 'Federal Funds Effective Rate',
            'GS10': '10-Year Treasury Constant Maturity Rate',
            'GS2': '2-Year Treasury Constant Maturity Rate',
            'GS30': '30-Year Treasury Constant Maturity Rate',
            
            # Money Supply
            'M1SL': 'M1 Money Stock',
            'M2SL': 'M2 Money Stock',
            'BASE': 'St. Louis Adjusted Monetary Base',
            
            # Consumer Metrics
            'UMCSENT': 'University of Michigan: Consumer Sentiment',
            'RSAFS': 'Advance Retail Sales: Retail and Food Services',
            'PI': 'Personal Income',
            'PSAVERT': 'Personal Saving Rate',
            
            # Housing
            'HOUST': 'Housing Starts: Total: New Privately Owned Housing Units Started',
            'CSUSHPISA': 'S&P/Case-Shiller U.S. National Home Price Index',
            'MORTGAGE30US': '30-Year Fixed Rate Mortgage Average in the United States',
            
            # Industrial
            'INDPRO': 'Industrial Production Index',
            'CAPUTLB50001SQ': 'Capacity Utilization: Total Industry',
            'NEWORDER': 'Manufacturers\' New Orders: Durable Goods',
            
            # International
            'DTWEXBGS': 'Trade Weighted U.S. Dollar Index: Broad, Goods and Services',
            'DEXUSEU': 'U.S. / Euro Foreign Exchange Rate',
            'DEXJPUS': 'Japan / U.S. Foreign Exchange Rate'
        }
