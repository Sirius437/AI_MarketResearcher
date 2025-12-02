"""
Euronext Amsterdam (XAMS) - Netherlands stocks.
"""

from ..models import Stock

# Netherlands stocks
XAMS_STOCKS = {
    # Netherlands - Technology
    "ASML.AS": Stock("ASML.AS", "ASML Holding N.V.", "XAMS", "Netherlands", "Technology", "Semiconductors", "large", "EUR", "Supplier of photolithography systems for semiconductor industry"),
    "ADYEN.AS": Stock("ADYEN.AS", "Adyen N.V.", "XAMS", "Netherlands", "Technology", "Payment Processing", "large", "EUR", "Payment technology platform"),
    
    # Netherlands - Consumer Staples
    "HEIA.AS": Stock("HEIA.AS", "Heineken N.V.", "XAMS", "Netherlands", "Consumer Staples", "Beverages", "large", "EUR", "Dutch brewing company"),
    "UNVR.AS": Stock("UNVR.AS", "Unilever N.V.", "XAMS", "Netherlands", "Consumer Staples", "Personal Care", "large", "EUR", "Dutch multinational consumer goods company"),
    
    # Netherlands - Energy
    "RDSA.AS": Stock("RDSA.AS", "Royal Dutch Shell plc", "XAMS", "Netherlands", "Energy", "Oil & Gas", "large", "EUR", "Dutch multinational oil and gas company"),
    
    # Netherlands - Financials
    "ING.AS": Stock("ING.AS", "ING Groep N.V.", "XAMS", "Netherlands", "Financials", "Banking", "large", "EUR", "Dutch multinational banking and financial services corporation"),
    "ABN.AS": Stock("ABN.AS", "ABN AMRO Group N.V.", "XAMS", "Netherlands", "Financials", "Banking", "large", "EUR", "Dutch bank"),
    
    # Netherlands - Industrials
    "AKZA.AS": Stock("AKZA.AS", "Akzo Nobel N.V.", "XAMS", "Netherlands", "Materials", "Chemicals", "large", "EUR", "Dutch multinational company"),
    "DSM.AS": Stock("DSM.AS", "Royal DSM", "XAMS", "Netherlands", "Materials", "Chemicals", "large", "EUR", "Dutch multinational corporation"),
    
    # Netherlands - Real Estate
    "UNA.AS": Stock("UNA.AS", "Unibail-Rodamco-Westfield", "XAMS", "Netherlands", "Real Estate", "REITs", "large", "EUR", "French commercial real estate company"),
}
