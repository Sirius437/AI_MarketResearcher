"""
Comprehensive global stocks database.
Contains detailed information about stocks across major global markets.
"""

from typing import Dict, List, Any
from .models import Stock
from .exchanges import (
    NASDAQ_STOCKS, NYSE_STOCKS, LSE_STOCKS, EURONEXT_STOCKS,
    TSE_STOCKS, KLSE_STOCKS, ASX_STOCKS, TSX_STOCKS,
    HKEX_STOCKS, SSE_STOCKS, BSE_STOCKS, KRX_STOCKS,
    PSE_STOCKS, VNX_STOCKS, XAMS_STOCKS, XETRA_STOCKS,
    XPAR_STOCKS, MIL_STOCKS, SIX_STOCKS, SZSE_STOCKS,
    NZX_STOCKS, JSE_STOCKS, EGX_STOCKS, TADAWUL_STOCKS,
    DFM_STOCKS, IDX_STOCKS, SET_STOCKS, SGX_STOCKS,
    TWSE_STOCKS
)


class StocksDatabase:
    """Database of global stocks organized by jurisdiction and sector."""
    
    def __init__(self):
        """Initialize stocks database."""
        # Combine all exchange-specific stock dictionaries
        self.stocks = {}
        self.stocks.update(NASDAQ_STOCKS)
        self.stocks.update(NYSE_STOCKS)
        self.stocks.update(LSE_STOCKS)
        self.stocks.update(EURONEXT_STOCKS)
        self.stocks.update(TSE_STOCKS)
        self.stocks.update(KLSE_STOCKS)
        self.stocks.update(ASX_STOCKS)
        self.stocks.update(TSX_STOCKS)
        self.stocks.update(HKEX_STOCKS)
        self.stocks.update(SSE_STOCKS)
        self.stocks.update(BSE_STOCKS)
        self.stocks.update(KRX_STOCKS)
        self.stocks.update(PSE_STOCKS)
        self.stocks.update(VNX_STOCKS)
        self.stocks.update(XAMS_STOCKS)
        self.stocks.update(XETRA_STOCKS)
        self.stocks.update(XPAR_STOCKS)
        self.stocks.update(MIL_STOCKS)
        self.stocks.update(SIX_STOCKS)
        self.stocks.update(SZSE_STOCKS)
        self.stocks.update(NZX_STOCKS)
        self.stocks.update(JSE_STOCKS)
        self.stocks.update(EGX_STOCKS)
        self.stocks.update(TADAWUL_STOCKS)
        self.stocks.update(DFM_STOCKS)
        self.stocks.update(IDX_STOCKS)
        self.stocks.update(SET_STOCKS)
        self.stocks.update(SGX_STOCKS)
        self.stocks.update(TWSE_STOCKS)
        
        # Sector mappings for easy filtering
        self.sector_mappings = {
            "Technology": ["Software", "Semiconductors", "Internet Services", "Consumer Electronics", "Cloud Computing", "Data Analytics", "Payment Processing", "Streaming Devices", "Video Communications", "Cloud Communications", "Identity Management", "Monitoring & Analytics", "Cybersecurity", "Web Infrastructure", "Edge Cloud Platform", "Solar Energy", "Hydrogen Fuel Cells", "Fuel Cells", "Music Streaming", "Software Development", "E-commerce Platform", "Ride Sharing", "Food Delivery", "Home Sharing", "Cryptocurrency Exchange", "Gaming Platform", "Business Software", "Digital Marketplace", "Real Estate Services", "Financial Technology", "IT Services", "Telecommunications Equipment", "Super App", "Gaming & E-commerce", "Social Media", "Video Streaming", "Cloud Accounting", "Logistics Software", "Medical Software", "Data Centers", "Buy Now Pay Later"],
            "Financials": ["Banking", "Investment Banking", "Insurance", "Payment Processing", "Financial Markets", "Islamic Banking"],
            "Healthcare": ["Pharmaceuticals", "Biotechnology", "Medical Devices", "Health Insurance", "Life Sciences", "Medical Technology", "Life Sciences Tools", "Medical Software"],
            "Energy": ["Oil & Gas", "Renewable Energy", "Oil & Gas Services", "LNG Transportation", "Renewable Fuels", "Chemicals"],
            "Consumer Discretionary": ["E-commerce", "Electric Vehicles", "Automotive", "Restaurants", "Home Improvement", "Online Retail", "Luxury Goods", "Apparel", "Auto Parts", "Gaming"],
            "Consumer Staples": ["Retail", "Food & Beverages", "Personal Care", "Food Products", "Tobacco", "Online Grocery"],
            "Communication Services": ["Telecommunications", "Streaming", "Social Media"],
            "Industrials": ["Conglomerate", "Aerospace", "Industrial Automation", "Construction", "Transportation", "Wind Energy"],
            "Materials": ["Mining", "Chemicals"],
            "Utilities": ["Electric Utilities", "Renewable Energy", "Infrastructure"],
            "Real Estate": ["REITs", "Real Estate Development"]
        }                                                   
        
        # Sector mappings for easy filtering
        self.sectors = {
            "Technology": ["Software", "Semiconductors", "Internet Services", "Consumer Electronics", "Cloud Computing", "Data Analytics", "Payment Processing", "Streaming Devices", "Video Communications", "Cloud Communications", "Identity Management", "Monitoring & Analytics", "Cybersecurity", "Web Infrastructure", "Edge Cloud Platform", "Solar Energy", "Hydrogen Fuel Cells", "Fuel Cells", "Music Streaming", "Software Development", "E-commerce Platform", "Ride Sharing", "Food Delivery", "Home Sharing", "Cryptocurrency Exchange", "Gaming Platform", "Business Software", "Digital Marketplace", "Real Estate Services", "Financial Technology", "IT Services", "Telecommunications Equipment", "Super App", "Gaming & E-commerce", "Social Media", "Video Streaming", "Cloud Accounting", "Logistics Software", "Medical Software", "Data Centers", "Buy Now Pay Later"],
            "Financials": ["Banking", "Investment Banking", "Insurance", "Payment Processing", "Financial Markets", "Islamic Banking"],
            "Healthcare": ["Pharmaceuticals", "Biotechnology", "Medical Devices", "Health Insurance", "Life Sciences", "Medical Technology", "Life Sciences Tools", "Medical Software"],
            "Energy": ["Oil & Gas", "Renewable Energy", "Oil & Gas Services", "LNG Transportation", "Renewable Fuels", "Chemicals"],
            "Consumer Discretionary": ["E-commerce", "Electric Vehicles", "Automotive", "Restaurants", "Home Improvement", "Online Retail", "Luxury Goods", "Apparel", "Auto Parts", "Gaming"],
            "Consumer Staples": ["Retail", "Food & Beverages", "Personal Care", "Food Products", "Tobacco", "Online Grocery"],
            "Communication Services": ["Telecommunications", "Streaming", "Social Media"],
            "Industrials": ["Conglomerate", "Aerospace", "Industrial Automation", "Construction", "Transportation", "Wind Energy"],
            "Materials": ["Mining", "Chemicals"],
            "Utilities": ["Electric Utilities", "Renewable Energy", "Infrastructure"],
            "Real Estate": ["REITs", "Real Estate Development"]
        }
    
    def get_stocks_by_jurisdiction(self, jurisdiction: str) -> List[Stock]:
        """Get all stocks for a specific jurisdiction."""
        return [stock for stock in self.stocks.values() 
                if stock.jurisdiction == jurisdiction]
    
    def get_stocks_by_sector(self, sector: str, jurisdiction: str = None) -> List[Stock]:
        """Get stocks by sector, optionally filtered by jurisdiction."""
        stocks = [stock for stock in self.stocks.values() if stock.sector == sector]
        if jurisdiction:
            stocks = [stock for stock in stocks if stock.jurisdiction == jurisdiction]
        return stocks
    
    def get_stocks_by_exchange(self, exchange: str) -> List[Stock]:
        """Get all stocks for a specific exchange."""
        return [stock for stock in self.stocks.values() 
                if stock.exchange == exchange]
    
    def get_stock_by_symbol(self, symbol: str) -> Stock:
        """Get stock by symbol."""
        return self.stocks.get(symbol.upper())
    
    def get_popular_stocks_by_jurisdiction(self, jurisdiction: str, limit: int = 10) -> List[Stock]:
        """Get popular (large cap) stocks by jurisdiction."""
        stocks = self.get_stocks_by_jurisdiction(jurisdiction)
        # Filter for large cap stocks
        large_cap_stocks = [stock for stock in stocks if stock.market_cap_category == "large"]
        return large_cap_stocks[:limit]
    
    def get_sectors_by_jurisdiction(self, jurisdiction: str) -> List[str]:
        """Get all sectors available in a jurisdiction."""
        stocks = self.get_stocks_by_jurisdiction(jurisdiction)
        return list(set(stock.sector for stock in stocks))
    
    def get_jurisdiction_summary(self, jurisdiction: str) -> Dict[str, Any]:
        """Get comprehensive summary of a jurisdiction."""
        stocks = self.get_stocks_by_jurisdiction(jurisdiction)
        if not stocks:
            return {}
        
        sectors = self.get_sectors_by_jurisdiction(jurisdiction)
        exchanges = list(set(stock.exchange for stock in stocks))
        currencies = list(set(stock.currency for stock in stocks))
        
        return {
            'jurisdiction': jurisdiction,
            'total_stocks': len(stocks),
            'sectors': sectors,
            'exchanges': exchanges,
            'currencies': currencies,
            'large_cap_count': len([s for s in stocks if s.market_cap_category == "large"]),
            'mid_cap_count': len([s for s in stocks if s.market_cap_category == "mid"]),
            'small_cap_count': len([s for s in stocks if s.market_cap_category == "small"])
        }
    
    def search_stocks(self, query: str, jurisdiction: str = None) -> List[Stock]:
        """Search stocks by name, symbol, or description."""
        query = query.lower()
        results = []
        
        for stock in self.stocks.values():
            if jurisdiction and stock.jurisdiction != jurisdiction:
                continue
                
            if (query in stock.symbol.lower() or 
                query in stock.name.lower() or 
                query in stock.description.lower() or
                query in stock.industry.lower()):
                results.append(stock)
        
        return results
    
    def get_all_jurisdictions(self) -> List[str]:
        """Get all available jurisdictions."""
        return list(set(stock.jurisdiction for stock in self.stocks.values()))
    
    def get_stocks_by_market_cap(self, category: str, jurisdiction: str = None) -> List[Stock]:
        """Get stocks by market cap category (large, mid, small)."""
        stocks = [stock for stock in self.stocks.values() 
                 if stock.market_cap_category == category]
        if jurisdiction:
            stocks = [stock for stock in stocks if stock.jurisdiction == jurisdiction]
        return stocks
