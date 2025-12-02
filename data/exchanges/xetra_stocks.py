"""
XETRA - Germany stocks.
"""

from ..models import Stock

# Germany stocks
XETRA_STOCKS = {
    # Germany - Technology
    "SAP.DE": Stock("SAP.DE", "SAP SE", "XETRA", "Germany", "Technology", "Software", "large", "EUR", "German multinational software corporation"),
    
    # Germany - Industrials
    "SIE.DE": Stock("SIE.DE", "Siemens AG", "XETRA", "Germany", "Industrials", "Conglomerate", "large", "EUR", "German multinational conglomerate"),
    "BMW.DE": Stock("BMW.DE", "Bayerische Motoren Werke AG", "XETRA", "Germany", "Consumer Discretionary", "Automotive", "large", "EUR", "German multinational manufacturer of luxury vehicles"),
    "VOW3.DE": Stock("VOW3.DE", "Volkswagen AG", "XETRA", "Germany", "Consumer Discretionary", "Automotive", "large", "EUR", "German multinational automotive manufacturing company"),
    "DAI.DE": Stock("DAI.DE", "Daimler AG", "XETRA", "Germany", "Consumer Discretionary", "Automotive", "large", "EUR", "German multinational automotive corporation"),
    
    # Germany - Financials
    "ALV.DE": Stock("ALV.DE", "Allianz SE", "XETRA", "Germany", "Financials", "Insurance", "large", "EUR", "German multinational financial services company"),
    "DBK.DE": Stock("DBK.DE", "Deutsche Bank AG", "XETRA", "Germany", "Financials", "Banking", "large", "EUR", "German multinational investment bank"),
    
    # Germany - Materials
    "BAS.DE": Stock("BAS.DE", "BASF SE", "XETRA", "Germany", "Materials", "Chemicals", "large", "EUR", "German multinational chemical company"),
    
    # Germany - Consumer Discretionary
    "ADS.DE": Stock("ADS.DE", "Adidas AG", "XETRA", "Germany", "Consumer Discretionary", "Apparel", "large", "EUR", "German multinational corporation that designs and manufactures shoes"),
    
    # Germany - Utilities
    "EOAN.DE": Stock("EOAN.DE", "E.ON SE", "XETRA", "Germany", "Utilities", "Electric Utilities", "large", "EUR", "German electric utility company"),
    
    # Germany - Healthcare
    "MRK.DE": Stock("MRK.DE", "Merck KGaA", "XETRA", "Germany", "Healthcare", "Pharmaceuticals", "large", "EUR", "German multinational science and technology company"),
    "FRE.DE": Stock("FRE.DE", "Fresenius SE & Co. KGaA", "XETRA", "Germany", "Healthcare", "Medical Services", "large", "EUR", "German multinational health care company"),
    
    # Germany - Technology
    "IFX.DE": Stock("IFX.DE", "Infineon Technologies AG", "XETRA", "Germany", "Technology", "Semiconductors", "large", "EUR", "German semiconductor manufacturer"),
}
