"""
Vietnam Stock Exchange (VNX) stocks.
"""

from ..models import Stock

# Vietnam Stock Exchange stocks
VNX_STOCKS = {
    # Vietnam - Banking
    "VCB.VN": Stock("VCB.VN", "Bank for Foreign Trade of Vietnam", "VNX", "Vietnam", "Financials", "Banking", "large", "VND", "Vietnamese commercial bank"),
    "BID.VN": Stock("BID.VN", "Bank for Investment and Development of Vietnam", "VNX", "Vietnam", "Financials", "Banking", "large", "VND", "Vietnamese state-owned commercial bank"),
    "CTG.VN": Stock("CTG.VN", "Vietnam Joint Stock Commercial Bank for Industry and Trade", "VNX", "Vietnam", "Financials", "Banking", "large", "VND", "Vietnamese commercial bank"),
    "TCB.VN": Stock("TCB.VN", "Vietnam Technological and Commercial Joint Stock Bank", "VNX", "Vietnam", "Financials", "Banking", "large", "VND", "Vietnamese commercial bank"),
    
    # Vietnam - Real Estate/Conglomerates
    "VIC.VN": Stock("VIC.VN", "Vingroup Joint Stock Company", "VNX", "Vietnam", "Real Estate", "Real Estate Development", "large", "VND", "Vietnamese conglomerate"),
    "VHM.VN": Stock("VHM.VN", "Vinhomes Joint Stock Company", "VNX", "Vietnam", "Real Estate", "Real Estate Development", "large", "VND", "Vietnamese real estate developer"),
    "VRE.VN": Stock("VRE.VN", "Vincom Retail Joint Stock Company", "VNX", "Vietnam", "Real Estate", "REITs", "large", "VND", "Vietnamese retail real estate company"),
    
    # Vietnam - Consumer/Retail
    "MSN.VN": Stock("MSN.VN", "Masan Group Corporation", "VNX", "Vietnam", "Consumer Staples", "Food Products", "large", "VND", "Vietnamese consumer goods company"),
    "VNM.VN": Stock("VNM.VN", "Vietnam Dairy Products Joint Stock Company", "VNX", "Vietnam", "Consumer Staples", "Food Products", "large", "VND", "Vietnamese dairy company"),
    
    # Vietnam - Energy/Utilities
    "GAS.VN": Stock("GAS.VN", "PetroVietnam Gas Joint Stock Corporation", "VNX", "Vietnam", "Energy", "Oil & Gas", "large", "VND", "Vietnamese gas company"),
    "POW.VN": Stock("POW.VN", "PetroVietnam Power Corporation", "VNX", "Vietnam", "Utilities", "Electric Utilities", "large", "VND", "Vietnamese power company"),
    
    # Vietnam - Technology
    "FPT.VN": Stock("FPT.VN", "FPT Corporation", "VNX", "Vietnam", "Technology", "IT Services", "large", "VND", "Vietnamese technology corporation"),
    
    # Vietnam - Steel/Materials
    "HPG.VN": Stock("HPG.VN", "Hoa Phat Group Joint Stock Company", "VNX", "Vietnam", "Materials", "Steel", "large", "VND", "Vietnamese steel company"),
}
