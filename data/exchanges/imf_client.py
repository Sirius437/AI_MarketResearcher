"""
International Monetary Fund (IMF) API client.
Provides access to global economic and financial data from the IMF.
"""

import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class IMFClient:
    """Client for International Monetary Fund (IMF) API."""
    
    def __init__(self, config: MarketResearcherConfig = None):
        """Initialize IMF client."""
        self.config = config
        self.base_url = "https://dataservices.imf.org/REST/SDMX_JSON.svc"
        self.session = None
        
        # Rate limiting: IMF API has generous limits but we'll be conservative
        self.request_times = []
        self.max_requests_per_minute = 60
        
        # IMF API is free and doesn't require API key
        logger.info("IMF API client initialized - no API key required")
    
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
        """Make request to IMF API."""
        await self._rate_limit_check()
        
        if not self.session:
            await self.initialize()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    logger.error(f"IMF API request failed: {response.status} - {error_text}")
                    return {"error": f"API request failed: {response.status}"}
                    
        except Exception as e:
            logger.error(f"IMF request error: {e}")
            return {"error": str(e)}
    
    async def get_datasets(self) -> Dict[str, Any]:
        """Get list of available IMF datasets."""
        return await self._make_request("Dataflow")
    
    async def get_data_structure(self, dataset_id: str) -> Dict[str, Any]:
        """Get data structure for a specific dataset."""
        return await self._make_request(f"DataStructure/{dataset_id}")
    
    async def get_code_list(self, dataset_id: str, dimension: str) -> Dict[str, Any]:
        """Get code list for a specific dimension in a dataset."""
        return await self._make_request(f"CodeList/{dataset_id}_{dimension}")
    
    async def get_compact_data(self, dataset_id: str, key: str = "", 
                              start_period: str = None, end_period: str = None) -> Dict[str, Any]:
        """Get compact data from IMF dataset."""
        endpoint = f"CompactData/{dataset_id}"
        if key:
            endpoint += f"/{key}"
        
        params = {}
        if start_period:
            params['startPeriod'] = start_period
        if end_period:
            params['endPeriod'] = end_period
        
        return await self._make_request(endpoint, params)
    
    async def get_ifs_data(self, country_code: str = "US", indicator: str = "NGDP_RPCH", 
                          start_year: int = None, end_year: int = None) -> Dict[str, Any]:
        """Get International Financial Statistics (IFS) data."""
        key = f"{country_code}.{indicator}.A"  # A = Annual
        
        params = {}
        if start_year:
            params['startPeriod'] = str(start_year)
        if end_year:
            params['endPeriod'] = str(end_year)
        
        return await self._make_request(f"CompactData/IFS/{key}", params)
    
    async def get_weo_data(self, country_code: str = "US", indicator: str = "NGDPRPC", 
                          start_year: int = None, end_year: int = None) -> Dict[str, Any]:
        """Get World Economic Outlook (WEO) data."""
        key = f"{country_code}.{indicator}"
        
        params = {}
        if start_year:
            params['startPeriod'] = str(start_year)
        if end_year:
            params['endPeriod'] = str(end_year)
        
        return await self._make_request(f"CompactData/WEO/{key}", params)
    
    async def get_dot_data(self, reporter_country: str = "US", partner_country: str = "W00", 
                          indicator: str = "TXG_FOB_USD", start_year: int = None, 
                          end_year: int = None) -> Dict[str, Any]:
        """Get Direction of Trade Statistics (DOTS) data."""
        key = f"{reporter_country}.{partner_country}.{indicator}.A"  # A = Annual
        
        params = {}
        if start_year:
            params['startPeriod'] = str(start_year)
        if end_year:
            params['endPeriod'] = str(end_year)
        
        return await self._make_request(f"CompactData/DOT/{key}", params)
    
    async def get_bop_data(self, country_code: str = "US", indicator: str = "BCA_BP6_USD", 
                          start_year: int = None, end_year: int = None) -> Dict[str, Any]:
        """Get Balance of Payments (BOP) data."""
        key = f"{country_code}.{indicator}.A"  # A = Annual
        
        params = {}
        if start_year:
            params['startPeriod'] = str(start_year)
        if end_year:
            params['endPeriod'] = str(end_year)
        
        return await self._make_request(f"CompactData/BOP/{key}", params)
    
    async def get_gfs_data(self, country_code: str = "US", indicator: str = "G1_G11_XDC", 
                          start_year: int = None, end_year: int = None) -> Dict[str, Any]:
        """Get Government Finance Statistics (GFS) data."""
        key = f"{country_code}.{indicator}.A"  # A = Annual
        
        params = {}
        if start_year:
            params['startPeriod'] = str(start_year)
        if end_year:
            params['endPeriod'] = str(end_year)
        
        return await self._make_request(f"CompactData/GFS/{key}", params)
    
    async def get_country_economic_indicators(self, country_code: str = "US", 
                                            years: int = 5) -> Dict[str, Any]:
        """Get key economic indicators for a country."""
        current_year = datetime.now().year
        start_year = current_year - years
        
        indicators = {
            'GDP Growth Rate': 'NGDP_RPCH',
            'GDP per Capita': 'NGDPRPC', 
            'Inflation Rate': 'PCPIPCH',
            'Unemployment Rate': 'LUR',
            'Current Account Balance': 'BCA_NGDPD',
            'Government Debt': 'GGXWDG_NGDP',
            'Export Volume': 'TXG_RPCH',
            'Import Volume': 'TMG_RPCH'
        }
        
        results = {}
        for name, indicator in indicators.items():
            try:
                # Try IFS first, then WEO
                data = await self.get_ifs_data(country_code, indicator, start_year, current_year)
                if 'error' in data or not self._extract_observations(data):
                    data = await self.get_weo_data(country_code, indicator, start_year, current_year)
                
                observations = self._extract_observations(data)
                if observations:
                    results[name] = {
                        'indicator': indicator,
                        'latest_value': observations[-1]['value'] if observations else None,
                        'latest_year': observations[-1]['period'] if observations else None,
                        'data': observations[-3:] if len(observations) >= 3 else observations  # Last 3 years
                    }
            except Exception as e:
                logger.error(f"Error fetching {name} for {country_code}: {e}")
                results[name] = {'error': str(e)}
        
        return results
    
    async def get_global_economic_outlook(self, years: int = 3) -> Dict[str, Any]:
        """Get global economic outlook data."""
        current_year = datetime.now().year
        start_year = current_year - 1
        end_year = current_year + years
        
        # Major economies
        countries = {
            'United States': 'US',
            'China': 'CN', 
            'Japan': 'JP',
            'Germany': 'DE',
            'United Kingdom': 'GB',
            'France': 'FR',
            'India': 'IN',
            'Italy': 'IT',
            'Brazil': 'BR',
            'Canada': 'CA'
        }
        
        results = {}
        for country_name, country_code in countries.items():
            try:
                gdp_data = await self.get_weo_data(country_code, 'NGDP_RPCH', start_year, end_year)
                inflation_data = await self.get_weo_data(country_code, 'PCPIPCH', start_year, end_year)
                
                gdp_obs = self._extract_observations(gdp_data)
                inflation_obs = self._extract_observations(inflation_data)
                
                results[country_name] = {
                    'country_code': country_code,
                    'gdp_growth': gdp_obs[-3:] if gdp_obs else [],
                    'inflation': inflation_obs[-3:] if inflation_obs else []
                }
            except Exception as e:
                logger.error(f"Error fetching outlook for {country_name}: {e}")
                results[country_name] = {'error': str(e)}
        
        return results
    
    async def get_exchange_rates(self, base_currency: str = "USD", years: int = 2) -> Dict[str, Any]:
        """Get exchange rate data from IMF."""
        current_year = datetime.now().year
        start_year = current_year - years
        
        # Major currency pairs
        currencies = ['EUR', 'JPY', 'GBP', 'CHF', 'CAD', 'AUD', 'CNY']
        
        results = {}
        for currency in currencies:
            try:
                # Exchange rate indicator in IFS
                indicator = f"ENDA_XDC_USD_RATE"  # End of period exchange rate
                data = await self.get_ifs_data(currency, indicator, start_year, current_year)
                
                observations = self._extract_observations(data)
                if observations:
                    results[f"{currency}/{base_currency}"] = {
                        'latest_rate': observations[-1]['value'] if observations else None,
                        'latest_period': observations[-1]['period'] if observations else None,
                        'historical': observations[-12:] if len(observations) >= 12 else observations
                    }
            except Exception as e:
                logger.error(f"Error fetching exchange rate for {currency}: {e}")
                results[f"{currency}/{base_currency}"] = {'error': str(e)}
        
        return results
    
    def _extract_observations(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract observations from IMF API response."""
        try:
            if 'CompactData' in data and 'DataSet' in data['CompactData']:
                dataset = data['CompactData']['DataSet']
                if 'Series' in dataset:
                    series = dataset['Series']
                    if isinstance(series, dict) and 'Obs' in series:
                        observations = series['Obs']
                        if isinstance(observations, list):
                            return [
                                {
                                    'period': obs.get('@TIME_PERIOD', ''),
                                    'value': float(obs.get('@OBS_VALUE', 0)) if obs.get('@OBS_VALUE') else None
                                }
                                for obs in observations
                                if obs.get('@OBS_VALUE') and obs.get('@OBS_VALUE') != ''
                            ]
                        elif isinstance(observations, dict):
                            return [{
                                'period': observations.get('@TIME_PERIOD', ''),
                                'value': float(observations.get('@OBS_VALUE', 0)) if observations.get('@OBS_VALUE') else None
                            }] if observations.get('@OBS_VALUE') else []
            return []
        except Exception as e:
            logger.error(f"Error extracting observations: {e}")
            return []
    
    def get_popular_indicators(self) -> Dict[str, Dict[str, str]]:
        """Get dictionary of popular IMF indicators by dataset."""
        return {
            'IFS': {
                'NGDP_RPCH': 'GDP Growth Rate (%)',
                'PCPIPCH': 'Inflation Rate (%)',
                'LUR': 'Unemployment Rate (%)',
                'FITB_PA': 'Current Account Balance (% of GDP)',
                'ENDA_XDC_USD_RATE': 'Exchange Rate (LCU per USD)',
                'FPOLM_PA': 'Policy Rate (%)',
                'FM_PA': 'Money Supply Growth (%)'
            },
            'WEO': {
                'NGDPRPC': 'GDP per Capita (USD)',
                'NGDP_RPCH': 'Real GDP Growth (%)',
                'PCPIPCH': 'Inflation Rate (%)',
                'LUR': 'Unemployment Rate (%)',
                'BCA_NGDPD': 'Current Account Balance (% of GDP)',
                'GGXWDG_NGDP': 'General Government Gross Debt (% of GDP)',
                'TXG_RPCH': 'Volume of Exports Growth (%)',
                'TMG_RPCH': 'Volume of Imports Growth (%)'
            },
            'BOP': {
                'BCA_BP6_USD': 'Current Account Balance (USD)',
                'BKA_BP6_USD': 'Capital Account Balance (USD)',
                'BFA_BP6_USD': 'Financial Account Balance (USD)',
                'BFDI_BP6_USD': 'Foreign Direct Investment (USD)',
                'BFPI_BP6_USD': 'Portfolio Investment (USD)'
            },
            'DOT': {
                'TXG_FOB_USD': 'Goods Exports (USD)',
                'TMG_CIF_USD': 'Goods Imports (USD)',
                'TX_FOB_USD': 'Total Exports (USD)',
                'TM_CIF_USD': 'Total Imports (USD)'
            },
            'GFS': {
                'G1_G11_XDC': 'Total Revenue',
                'G2_G21_XDC': 'Total Expenditure', 
                'GSD_G1_G2_XDC': 'Net Operating Balance',
                'G4_G41_XDC': 'Net Investment in Assets',
                'GFSBALANCE_G1_G2_G31_G32_XDC': 'Overall Balance'
            }
        }
    
    def get_country_codes(self) -> Dict[str, str]:
        """Get common country codes used in IMF data."""
        return {
            'US': 'United States',
            'CN': 'China',
            'JP': 'Japan', 
            'DE': 'Germany',
            'GB': 'United Kingdom',
            'FR': 'France',
            'IN': 'India',
            'IT': 'Italy',
            'BR': 'Brazil',
            'CA': 'Canada',
            'RU': 'Russia',
            'KR': 'South Korea',
            'AU': 'Australia',
            'ES': 'Spain',
            'MX': 'Mexico',
            'ID': 'Indonesia',
            'NL': 'Netherlands',
            'SA': 'Saudi Arabia',
            'TR': 'Turkey',
            'TW': 'Taiwan',
            'CH': 'Switzerland',
            'BE': 'Belgium',
            'AR': 'Argentina',
            'IE': 'Ireland',
            'IL': 'Israel',
            'TH': 'Thailand',
            'EG': 'Egypt',
            'NG': 'Nigeria',
            'BD': 'Bangladesh',
            'VN': 'Vietnam',
            'PH': 'Philippines',
            'MY': 'Malaysia',
            'SG': 'Singapore',
            'ZA': 'South Africa',
            'CL': 'Chile',
            'FI': 'Finland',
            'DK': 'Denmark',
            'NO': 'Norway',
            'NZ': 'New Zealand',
            'PT': 'Portugal',
            'CZ': 'Czech Republic',
            'RO': 'Romania',
            'PE': 'Peru',
            'GR': 'Greece',
            'HU': 'Hungary'
        }
