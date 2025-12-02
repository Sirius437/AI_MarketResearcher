"""
Dubai Financial Market (DFM) - UAE stocks.
"""

from ..models import Stock

# UAE stocks
DFM_STOCKS = {
    # UAE - Banking
    "ADCB.DU": Stock("ADCB.DU", "Abu Dhabi Commercial Bank PJSC", "DFM", "UAE", "Financials", "Banking", "large", "AED", "UAE commercial bank"),
    "FAB.DU": Stock("FAB.DU", "First Abu Dhabi Bank PJSC", "DFM", "UAE", "Financials", "Banking", "large", "AED", "UAE's largest bank"),
    "DIB.DU": Stock("DIB.DU", "Dubai Islamic Bank PJSC", "DFM", "UAE", "Financials", "Islamic Banking", "large", "AED", "UAE Islamic bank"),
    
    # UAE - Real Estate
    "EMAAR.DU": Stock("EMAAR.DU", "Emaar Properties PJSC", "DFM", "UAE", "Real Estate", "Real Estate Development", "large", "AED", "UAE real estate development company"),
    "ALDAR.DU": Stock("ALDAR.DU", "Aldar Properties PJSC", "DFM", "UAE", "Real Estate", "Real Estate Development", "large", "AED", "UAE real estate company"),
    
    # UAE - Telecommunications
    "ETISALAT.DU": Stock("ETISALAT.DU", "Emirates Telecommunications Group Company PJSC", "DFM", "UAE", "Communication Services", "Telecommunications", "large", "AED", "UAE telecommunications company"),
    "DU.DU": Stock("DU.DU", "Emirates Integrated Telecommunications Company PJSC", "DFM", "UAE", "Communication Services", "Telecommunications", "large", "AED", "UAE telecommunications company"),
    
    # UAE - Airlines
    "EMIRATES.DU": Stock("EMIRATES.DU", "Emirates Group", "DFM", "UAE", "Industrials", "Airlines", "large", "AED", "UAE airline company"),
    
    # UAE - Energy
    "ADNOC.DU": Stock("ADNOC.DU", "Abu Dhabi National Oil Company", "DFM", "UAE", "Energy", "Oil & Gas", "large", "AED", "UAE state oil company"),
}
