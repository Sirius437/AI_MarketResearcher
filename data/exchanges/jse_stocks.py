"""
Johannesburg Stock Exchange (JSE) - South Africa stocks.
"""

from ..models import Stock

# South Africa stocks
JSE_STOCKS = {
    # South Africa - Mining
    "AGL.JO": Stock("AGL.JO", "Anglo American plc", "JSE", "South Africa", "Materials", "Mining", "large", "ZAR", "British multinational mining company"),
    "BHP.JO": Stock("BHP.JO", "BHP Group Limited", "JSE", "South Africa", "Materials", "Mining", "large", "ZAR", "Australian multinational mining company"),
    "GFI.JO": Stock("GFI.JO", "Gold Fields Limited", "JSE", "South Africa", "Materials", "Mining", "large", "ZAR", "South African gold mining company"),
    "AMS.JO": Stock("AMS.JO", "Anglo American Platinum Limited", "JSE", "South Africa", "Materials", "Mining", "large", "ZAR", "South African platinum mining company"),
    
    # South Africa - Banking
    "SBK.JO": Stock("SBK.JO", "Standard Bank Group Limited", "JSE", "South Africa", "Financials", "Banking", "large", "ZAR", "South African banking and financial services group"),
    "FSR.JO": Stock("FSR.JO", "FirstRand Limited", "JSE", "South Africa", "Financials", "Banking", "large", "ZAR", "South African financial services group"),
    "ABG.JO": Stock("ABG.JO", "ABSA Group Limited", "JSE", "South Africa", "Financials", "Banking", "large", "ZAR", "South African multinational banking group"),
    "NED.JO": Stock("NED.JO", "Nedbank Group Limited", "JSE", "South Africa", "Financials", "Banking", "large", "ZAR", "South African banking group"),
    
    # South Africa - Retail
    "SHP.JO": Stock("SHP.JO", "Shoprite Holdings Limited", "JSE", "South Africa", "Consumer Staples", "Retail", "large", "ZAR", "South African retail group"),
    "WHL.JO": Stock("WHL.JO", "Woolworths Holdings Limited", "JSE", "South Africa", "Consumer Discretionary", "Retail", "large", "ZAR", "South African retail group"),
    
    # South Africa - Telecommunications
    "MTN.JO": Stock("MTN.JO", "MTN Group Limited", "JSE", "South Africa", "Communication Services", "Telecommunications", "large", "ZAR", "South African multinational mobile telecommunications company"),
    "VOD.JO": Stock("VOD.JO", "Vodacom Group Limited", "JSE", "South Africa", "Communication Services", "Telecommunications", "large", "ZAR", "South African mobile communications company"),
    
    # South Africa - Consumer Goods
    "SAB.JO": Stock("SAB.JO", "SABMiller plc", "JSE", "South Africa", "Consumer Staples", "Beverages", "large", "ZAR", "South African brewing and beverage company"),
    "RMH.JO": Stock("RMH.JO", "RMB Holdings Limited", "JSE", "South Africa", "Financials", "Investment Services", "large", "ZAR", "South African investment holding company"),
}
