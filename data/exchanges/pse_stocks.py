"""
Philippine Stock Exchange (PSE) stocks.
"""

from ..models import Stock

# Philippine Stock Exchange stocks
PSE_STOCKS = {
    # Philippines - Banking
    "BDO.PS": Stock("BDO.PS", "BDO Unibank Inc.", "PSE", "Philippines", "Financials", "Banking", "large", "PHP", "Philippine universal bank"),
    "BPI.PS": Stock("BPI.PS", "Bank of the Philippine Islands", "PSE", "Philippines", "Financials", "Banking", "large", "PHP", "Philippine universal bank"),
    "MBT.PS": Stock("MBT.PS", "Metropolitan Bank & Trust Company", "PSE", "Philippines", "Financials", "Banking", "large", "PHP", "Philippine commercial bank"),
    "SECB.PS": Stock("SECB.PS", "Security Bank Corporation", "PSE", "Philippines", "Financials", "Banking", "large", "PHP", "Philippine universal bank"),
    
    # Philippines - Conglomerates
    "SM.PS": Stock("SM.PS", "SM Investments Corporation", "PSE", "Philippines", "Consumer Discretionary", "Retail", "large", "PHP", "Philippine conglomerate"),
    "JGS.PS": Stock("JGS.PS", "JG Summit Holdings Inc.", "PSE", "Philippines", "Industrials", "Conglomerate", "large", "PHP", "Philippine conglomerate"),
    "DMC.PS": Stock("DMC.PS", "DMCI Holdings Inc.", "PSE", "Philippines", "Industrials", "Construction", "large", "PHP", "Philippine conglomerate"),
    "AEV.PS": Stock("AEV.PS", "Aboitiz Equity Ventures Inc.", "PSE", "Philippines", "Industrials", "Conglomerate", "large", "PHP", "Philippine conglomerate"),
    
    # Philippines - Consumer/Food
    "JFC.PS": Stock("JFC.PS", "Jollibee Foods Corporation", "PSE", "Philippines", "Consumer Discretionary", "Restaurants", "large", "PHP", "Philippine multinational chain of fast food restaurants"),
    "URC.PS": Stock("URC.PS", "Universal Robina Corporation", "PSE", "Philippines", "Consumer Staples", "Food Products", "large", "PHP", "Philippine food and beverage company"),
    "CNPF.PS": Stock("CNPF.PS", "Century Pacific Food Inc.", "PSE", "Philippines", "Consumer Staples", "Food Products", "large", "PHP", "Philippine food company"),
    
    # Philippines - Telecommunications
    "PLDT.PS": Stock("PLDT.PS", "Philippine Long Distance Telephone Company", "PSE", "Philippines", "Communication Services", "Telecommunications", "large", "PHP", "Philippine telecommunications company"),
    "TEL.PS": Stock("TEL.PS", "Globe Telecom Inc.", "PSE", "Philippines", "Communication Services", "Telecommunications", "large", "PHP", "Philippine telecommunications company"),
    
    # Philippines - Real Estate
    "ALI.PS": Stock("ALI.PS", "Ayala Land Inc.", "PSE", "Philippines", "Real Estate", "Real Estate Development", "large", "PHP", "Philippine real estate company"),
    "MEG.PS": Stock("MEG.PS", "Megaworld Corporation", "PSE", "Philippines", "Real Estate", "Real Estate Development", "large", "PHP", "Philippine real estate company"),
    "SMPH.PS": Stock("SMPH.PS", "SM Prime Holdings Inc.", "PSE", "Philippines", "Real Estate", "Real Estate Development", "large", "PHP", "Philippine real estate company"),
    
    # Philippines - Utilities/Energy
    "AC.PS": Stock("AC.PS", "Ayala Corporation", "PSE", "Philippines", "Industrials", "Conglomerate", "large", "PHP", "Philippine conglomerate"),
    "AP.PS": Stock("AP.PS", "Aboitiz Power Corporation", "PSE", "Philippines", "Utilities", "Electric Utilities", "large", "PHP", "Philippine power company"),
}
