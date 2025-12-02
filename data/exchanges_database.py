"""
Global stock exchanges database.
Contains comprehensive information about major stock exchanges worldwide.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class Exchange:
    """Stock exchange information."""
    code: str
    name: str
    country: str
    jurisdiction: str
    currency: str
    timezone: str
    suffix: str
    trading_hours: str
    website: str


class ExchangesDatabase:
    """Database of global stock exchanges."""
    
    def __init__(self):
        """Initialize exchanges database."""
        self.exchanges = {
            # United States
            "NYSE": Exchange(
                code="NYSE",
                name="New York Stock Exchange",
                country="United States",
                jurisdiction="US",
                currency="USD",
                timezone="America/New_York",
                suffix="",
                trading_hours="09:30-16:00 EST",
                website="https://www.nyse.com"
            ),
            "NASDAQ": Exchange(
                code="NASDAQ",
                name="NASDAQ Stock Market",
                country="United States",
                jurisdiction="US",
                currency="USD",
                timezone="America/New_York",
                suffix="",
                trading_hours="09:30-16:00 EST",
                website="https://www.nasdaq.com"
            ),
            
            # European Union
            "XAMS": Exchange(
                code="XAMS",
                name="Euronext Amsterdam",
                country="Netherlands",
                jurisdiction="EU",
                currency="EUR",
                timezone="Europe/Amsterdam",
                suffix=".AS",
                trading_hours="09:00-17:30 CET",
                website="https://www.euronext.com"
            ),
            "XPAR": Exchange(
                code="XPAR",
                name="Euronext Paris",
                country="France",
                jurisdiction="EU",
                currency="EUR",
                timezone="Europe/Paris",
                suffix=".PA",
                trading_hours="09:00-17:30 CET",
                website="https://www.euronext.com"
            ),
            "XETR": Exchange(
                code="XETR",
                name="XETRA (Deutsche Börse)",
                country="Germany",
                jurisdiction="EU",
                currency="EUR",
                timezone="Europe/Berlin",
                suffix=".DE",
                trading_hours="09:00-17:30 CET",
                website="https://www.deutsche-boerse.com"
            ),
            "SWX": Exchange(
                code="SWX",
                name="SIX Swiss Exchange",
                country="Switzerland",
                jurisdiction="EU",
                currency="CHF",
                timezone="Europe/Zurich",
                suffix=".SW",
                trading_hours="09:00-17:30 CET",
                website="https://www.six-group.com"
            ),
            
            # United Kingdom
            "LSE": Exchange(
                code="LSE",
                name="London Stock Exchange",
                country="United Kingdom",
                jurisdiction="UK",
                currency="GBP",
                timezone="Europe/London",
                suffix=".L",
                trading_hours="08:00-16:30 GMT",
                website="https://www.londonstockexchange.com"
            ),
            
            # Asia Pacific
            "TSE": Exchange(
                code="TSE",
                name="Tokyo Stock Exchange",
                country="Japan",
                jurisdiction="Asia",
                currency="JPY",
                timezone="Asia/Tokyo",
                suffix=".T",
                trading_hours="09:00-15:00 JST",
                website="https://www.jpx.co.jp"
            ),
            "KRX": Exchange(
                code="KRX",
                name="Korea Exchange",
                country="South Korea",
                jurisdiction="Asia",
                currency="KRW",
                timezone="Asia/Seoul",
                suffix=".KS",
                trading_hours="09:00-15:30 KST",
                website="https://www.krx.co.kr"
            ),
            "TWSE": Exchange(
                code="TWSE",
                name="Taiwan Stock Exchange",
                country="Taiwan",
                jurisdiction="Asia",
                currency="TWD",
                timezone="Asia/Taipei",
                suffix=".TW",
                trading_hours="09:00-13:30 CST",
                website="https://www.twse.com.tw"
            ),
            "HKEX": Exchange(
                code="HKEX",
                name="Hong Kong Stock Exchange",
                country="Hong Kong",
                jurisdiction="Asia",
                currency="HKD",
                timezone="Asia/Hong_Kong",
                suffix=".HK",
                trading_hours="09:30-16:00 HKT",
                website="https://www.hkex.com.hk"
            ),
            "SSE": Exchange(
                code="SSE",
                name="Shanghai Stock Exchange",
                country="China",
                jurisdiction="Asia",
                currency="CNY",
                timezone="Asia/Shanghai",
                suffix=".SS",
                trading_hours="09:30-15:00 CST",
                website="https://www.sse.com.cn"
            ),
            "SZSE": Exchange(
                code="SZSE",
                name="Shenzhen Stock Exchange",
                country="China",
                jurisdiction="Asia",
                currency="CNY",
                timezone="Asia/Shanghai",
                suffix=".SZ",
                trading_hours="09:30-15:00 CST",
                website="https://www.szse.cn"
            ),
            
            # Australia & New Zealand
            "ASX": Exchange(
                code="ASX",
                name="Australian Securities Exchange",
                country="Australia",
                jurisdiction="Australia/NZ",
                currency="AUD",
                timezone="Australia/Sydney",
                suffix=".AX",
                trading_hours="10:00-16:00 AEST",
                website="https://www.asx.com.au"
            ),
            "NZX": Exchange(
                code="NZX",
                name="New Zealand Exchange",
                country="New Zealand",
                jurisdiction="Australia/NZ",
                currency="NZD",
                timezone="Pacific/Auckland",
                suffix=".NZ",
                trading_hours="10:00-16:45 NZST",
                website="https://www.nzx.com"
            ),
            
            # Middle East & North Africa
            "TADAWUL": Exchange(
                code="TADAWUL",
                name="Saudi Stock Exchange",
                country="Saudi Arabia",
                jurisdiction="MENA",
                currency="SAR",
                timezone="Asia/Riyadh",
                suffix=".SR",
                trading_hours="10:00-15:00 AST",
                website="https://www.saudiexchange.sa"
            ),
            "ADX": Exchange(
                code="ADX",
                name="Abu Dhabi Securities Exchange",
                country="United Arab Emirates",
                jurisdiction="MENA",
                currency="AED",
                timezone="Asia/Dubai",
                suffix=".AD",
                trading_hours="10:00-15:00 GST",
                website="https://www.adx.ae"
            ),
            "EGX": Exchange(
                code="EGX",
                name="Egyptian Exchange",
                country="Egypt",
                jurisdiction="MENA",
                currency="EGP",
                timezone="Africa/Cairo",
                suffix=".CA",
                trading_hours="10:00-14:30 EET",
                website="https://www.egx.com.eg"
            ),
            "DFM": Exchange(
                code="DFM",
                name="Dubai Financial Market",
                country="United Arab Emirates",
                jurisdiction="MENA",
                currency="AED",
                timezone="Asia/Dubai",
                suffix=".DU",
                trading_hours="10:00-15:00 GST",
                website="https://www.dfm.ae"
            ),
            "QE": Exchange(
                code="QE",
                name="Qatar Exchange",
                country="Qatar",
                jurisdiction="MENA",
                currency="QAR",
                timezone="Asia/Qatar",
                suffix=".QA",
                trading_hours="09:30-13:00 AST",
                website="https://www.qe.com.qa"
            ),
            
            # South Africa
            "JSE": Exchange(
                code="JSE",
                name="Johannesburg Stock Exchange",
                country="South Africa",
                jurisdiction="Africa",
                currency="ZAR",
                timezone="Africa/Johannesburg",
                suffix=".JO",
                trading_hours="09:00-17:00 SAST",
                website="https://www.jse.co.za"
            ),
            
            # Additional Asian Countries
            "KLSE": Exchange(
                code="KLSE",
                name="Bursa Malaysia",
                country="Malaysia",
                jurisdiction="Asia",
                currency="MYR",
                timezone="Asia/Kuala_Lumpur",
                suffix=".KL",
                trading_hours="09:00-17:00 MYT",
                website="https://www.bursamalaysia.com"
            ),
            "IDX": Exchange(
                code="IDX",
                name="Indonesia Stock Exchange",
                country="Indonesia",
                jurisdiction="Asia",
                currency="IDR",
                timezone="Asia/Jakarta",
                suffix=".JK",
                trading_hours="09:00-16:00 WIB",
                website="https://www.idx.co.id"
            ),
            "SET": Exchange(
                code="SET",
                name="Stock Exchange of Thailand",
                country="Thailand",
                jurisdiction="Asia",
                currency="THB",
                timezone="Asia/Bangkok",
                suffix=".BK",
                trading_hours="10:00-16:30 ICT",
                website="https://www.set.or.th"
            ),
            "BSE": Exchange(
                code="BSE",
                name="Bombay Stock Exchange",
                country="India",
                jurisdiction="Asia",
                currency="INR",
                timezone="Asia/Kolkata",
                suffix=".BO",
                trading_hours="09:15-15:30 IST",
                website="https://www.bseindia.com"
            ),
            "NSE": Exchange(
                code="NSE",
                name="National Stock Exchange of India",
                country="India",
                jurisdiction="Asia",
                currency="INR",
                timezone="Asia/Kolkata",
                suffix=".NS",
                trading_hours="09:15-15:30 IST",
                website="https://www.nseindia.com"
            ),
            "SGX": Exchange(
                code="SGX",
                name="Singapore Exchange",
                country="Singapore",
                jurisdiction="Asia",
                currency="SGD",
                timezone="Asia/Singapore",
                suffix=".SI",
                trading_hours="09:00-17:00 SGT",
                website="https://www.sgx.com"
            ),
            "PSE": Exchange(
                code="PSE",
                name="Philippine Stock Exchange",
                country="Philippines",
                jurisdiction="Asia",
                currency="PHP",
                timezone="Asia/Manila",
                suffix=".PS",
                trading_hours="09:30-15:30 PHT",
                website="https://www.pse.com.ph"
            ),
            "VNX": Exchange(
                code="VNX",
                name="Ho Chi Minh Stock Exchange",
                country="Vietnam",
                jurisdiction="Asia",
                currency="VND",
                timezone="Asia/Ho_Chi_Minh",
                suffix=".VN",
                trading_hours="09:00-15:00 ICT",
                website="https://www.hsx.vn"
            )
        }
    
    def get_exchanges_by_jurisdiction(self, jurisdiction: str) -> List[Exchange]:
        """Get all exchanges for a specific jurisdiction."""
        return [exchange for exchange in self.exchanges.values() 
                if exchange.jurisdiction == jurisdiction]
    
    def get_exchange_by_code(self, code: str) -> Exchange:
        """Get exchange by code."""
        return self.exchanges.get(code.upper())
    
    def get_exchange_by_suffix(self, suffix: str) -> Exchange:
        """Get exchange by symbol suffix."""
        for exchange in self.exchanges.values():
            if exchange.suffix == suffix:
                return exchange
        return None
    
    def get_all_jurisdictions(self) -> List[str]:
        """Get all available jurisdictions."""
        return list(set(exchange.jurisdiction for exchange in self.exchanges.values()))
    
    def get_jurisdiction_info(self, jurisdiction: str) -> Dict[str, Any]:
        """Get comprehensive information about a jurisdiction."""
        exchanges = self.get_exchanges_by_jurisdiction(jurisdiction)
        if not exchanges:
            return {}
        
        return {
            'jurisdiction': jurisdiction,
            'exchanges': [
                {
                    'code': ex.code,
                    'name': ex.name,
                    'country': ex.country,
                    'currency': ex.currency,
                    'suffix': ex.suffix,
                    'trading_hours': ex.trading_hours
                }
                for ex in exchanges
            ],
            'countries': list(set(ex.country for ex in exchanges)),
            'currencies': list(set(ex.currency for ex in exchanges))
        }
