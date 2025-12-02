"""
Egyptian Exchange (EGX) - Egypt stocks.
"""

from ..models import Stock

# Egypt stocks
EGX_STOCKS = {
    # Egypt - Banking
    "CIB.CA": Stock("CIB.CA", "Commercial International Bank Egypt S.A.E.", "EGX", "Egypt", "Financials", "Banking", "large", "EGP", "Egyptian commercial bank"),
    "COMI.CA": Stock("COMI.CA", "Commercial International Bank", "EGX", "Egypt", "Financials", "Banking", "large", "EGP", "Egyptian multinational bank"),
    
    # Egypt - Telecommunications
    "ORTE.CA": Stock("ORTE.CA", "Orange Egypt", "EGX", "Egypt", "Communication Services", "Telecommunications", "large", "EGP", "Egyptian telecommunications company"),
    
    # Egypt - Consumer Goods
    "JUFO.CA": Stock("JUFO.CA", "Juhayna Food Industries", "EGX", "Egypt", "Consumer Staples", "Food Products", "large", "EGP", "Egyptian food and beverage company"),
    "EAST.CA": Stock("EAST.CA", "Eastern Company S.A.E.", "EGX", "Egypt", "Consumer Staples", "Tobacco", "large", "EGP", "Egyptian tobacco company"),
    
    # Egypt - Real Estate
    "TALAAT.CA": Stock("TALAAT.CA", "Talaat Moustafa Group Holding", "EGX", "Egypt", "Real Estate", "Real Estate Development", "large", "EGP", "Egyptian real estate development company"),
    "PALM.CA": Stock("PALM.CA", "Palm Hills Developments S.A.E.", "EGX", "Egypt", "Real Estate", "Real Estate Development", "large", "EGP", "Egyptian real estate company"),
    
    # Egypt - Materials
    "SWDY.CA": Stock("SWDY.CA", "El Sewedy Electric Company", "EGX", "Egypt", "Industrials", "Electrical Equipment", "large", "EGP", "Egyptian electrical equipment manufacturer"),
    
    # Egypt - Energy
    "EGPC.CA": Stock("EGPC.CA", "Egyptian General Petroleum Corporation", "EGX", "Egypt", "Energy", "Oil & Gas", "large", "EGP", "Egyptian state-owned oil company"),
}
