"""
New Zealand Exchange (NZX) stocks.
"""

from ..models import Stock

# New Zealand stocks
NZX_STOCKS = {
    # New Zealand - Financial Services
    "ANZ.NZ": Stock("ANZ.NZ", "ANZ Group Holdings Limited", "NZX", "New Zealand", "Financials", "Banking", "large", "NZD", "Major Australasian bank"),
    "HGH.NZ": Stock("HGH.NZ", "Heartland Group Holdings Limited", "NZX", "New Zealand", "Financials", "Banking", "mid", "NZD", "New Zealand bank and financial services provider"),
    "NZX.NZ": Stock("NZX.NZ", "NZX Limited", "NZX", "New Zealand", "Financials", "Financial Exchanges", "mid", "NZD", "New Zealand stock exchange operator"),
    "WBC.NZ": Stock("WBC.NZ", "Westpac Banking Corporation", "NZX", "New Zealand", "Financials", "Banking", "large", "NZD", "Major Australasian bank"),
    "AMP.NZ": Stock("AMP.NZ", "AMP Limited", "NZX", "New Zealand", "Financials", "Financial Services", "large", "NZD", "Financial services provider"),
    "MHJ.NZ": Stock("MHJ.NZ", "Michael Hill International Limited", "NZX", "New Zealand", "Consumer Discretionary", "Retail", "mid", "NZD", "Jewelry retail company"),
    "VGL.NZ": Stock("VGL.NZ", "Vista Group International Limited", "NZX", "New Zealand", "Technology", "Software", "mid", "NZD", "Cinema software provider"),
    "ASF.NZ": Stock("ASF.NZ", "Asset Plus Limited", "NZX", "New Zealand", "Real Estate", "REITs", "small", "NZD", "Property investment company"),
    
    # New Zealand - Communication Services
    "SPK.NZ": Stock("SPK.NZ", "Spark New Zealand Limited", "NZX", "New Zealand", "Communication Services", "Telecommunications", "large", "NZD", "New Zealand telecommunications company"),
    "CHO.NZ": Stock("CHO.NZ", "Chorus Limited", "NZX", "New Zealand", "Communication Services", "Telecommunications", "large", "NZD", "New Zealand telecommunications infrastructure"),
    "SKT.NZ": Stock("SKT.NZ", "Sky Network Television Limited", "NZX", "New Zealand", "Communication Services", "Media", "mid", "NZD", "Pay television broadcaster"),
    "TLS.NZ": Stock("TLS.NZ", "Telstra Corporation Limited", "NZX", "New Zealand", "Communication Services", "Telecommunications", "large", "NZD", "Telecommunications provider"),
    
    # New Zealand - Utilities
    "CEN.NZ": Stock("CEN.NZ", "Contact Energy Limited", "NZX", "New Zealand", "Utilities", "Electric Utilities", "large", "NZD", "New Zealand electricity generator and retailer"),
    "MCY.NZ": Stock("MCY.NZ", "Mercury NZ Limited", "NZX", "New Zealand", "Utilities", "Electric Utilities", "large", "NZD", "New Zealand electricity generator and retailer"),
    "TPW.NZ": Stock("TPW.NZ", "Trustpower Limited", "NZX", "New Zealand", "Utilities", "Electric Utilities", "large", "NZD", "New Zealand electricity retailer"),
    "VCT.NZ": Stock("VCT.NZ", "Vector Limited", "NZX", "New Zealand", "Utilities", "Infrastructure", "large", "NZD", "New Zealand infrastructure company"),
    
    # New Zealand - Healthcare
    "FPH.NZ": Stock("FPH.NZ", "Fisher & Paykel Healthcare Corporation Limited", "NZX", "New Zealand", "Healthcare", "Medical Devices", "large", "NZD", "New Zealand medical device company"),
    "AFT.NZ": Stock("AFT.NZ", "AFT Pharmaceuticals Limited", "NZX", "New Zealand", "Healthcare", "Pharmaceuticals", "mid", "NZD", "New Zealand pharmaceutical company"),
    "GXH.NZ": Stock("GXH.NZ", "Green Cross Health Limited", "NZX", "New Zealand", "Healthcare", "Healthcare Services", "mid", "NZD", "New Zealand healthcare services provider"),
    "PEB.NZ": Stock("PEB.NZ", "Pacific Edge Limited", "NZX", "New Zealand", "Healthcare", "Biotechnology", "mid", "NZD", "New Zealand biotechnology company"),
    "ARG.NZ": Stock("ARG.NZ", "Argosy Property Limited", "NZX", "New Zealand", "Healthcare", "Healthcare REITs", "mid", "NZD", "Healthcare property investor"),
    "RAD.NZ": Stock("RAD.NZ", "Radius Care Limited", "NZX", "New Zealand", "Healthcare", "Healthcare Services", "small", "NZD", "Aged care and retirement village operator"),
    
    # New Zealand - Technology
    "GTK.NZ": Stock("GTK.NZ", "Gentrack Group Limited", "NZX", "New Zealand", "Technology", "Software", "large", "NZD", "New Zealand software company"),
    "IKE.NZ": Stock("IKE.NZ", "ikeGPS Group Limited", "NZX", "New Zealand", "Technology", "Hardware", "mid", "NZD", "New Zealand technology hardware company"),
    "SKO.NZ": Stock("SKO.NZ", "Serko Limited", "NZX", "New Zealand", "Technology", "Software", "mid", "NZD", "New Zealand travel software company"),
    "SPY.NZ": Stock("SPY.NZ", "Smartpay Holdings Limited", "NZX", "New Zealand", "Technology", "Payment Solutions", "mid", "NZD", "New Zealand payment solutions provider"),
    "PYS.NZ": Stock("PYS.NZ", "Plexure Group Limited", "NZX", "New Zealand", "Technology", "Software", "small", "NZD", "Mobile engagement software provider"),
    "RUA.NZ": Stock("RUA.NZ", "Rakon Limited", "NZX", "New Zealand", "Technology", "Hardware", "mid", "NZD", "Technology components manufacturer"),
    "EVO.NZ": Stock("EVO.NZ", "EROAD Limited", "NZX", "New Zealand", "Technology", "Software", "mid", "NZD", "Fleet management software provider"),
    
    # New Zealand - Primary Industries
    "SAN.NZ": Stock("SAN.NZ", "Sanford Limited", "NZX", "New Zealand", "Consumer Staples", "Food Products", "mid", "NZD", "New Zealand fishing company"),
    "NZK.NZ": Stock("NZK.NZ", "New Zealand King Salmon Investments Limited", "NZX", "New Zealand", "Consumer Staples", "Food Products", "small", "NZD", "Salmon farming company"),
    "SEK.NZ": Stock("SEK.NZ", "Seeka Limited", "NZX", "New Zealand", "Consumer Staples", "Food Products", "small", "NZD", "Fruit and produce company"),
    "DGL.NZ": Stock("DGL.NZ", "Delegat Group Limited", "NZX", "New Zealand", "Consumer Staples", "Beverages", "mid", "NZD", "Wine producer and exporter"),
    
    # New Zealand - Consumer
    # Consumer Staples
    "ATM.NZ": Stock("ATM.NZ", "The a2 Milk Company Limited", "NZX", "New Zealand", "Consumer Staples", "Food Products", "large", "NZD", "New Zealand dairy company"),
    "FCG.NZ": Stock("FCG.NZ", "Fonterra Co-operative Group Limited", "NZX", "New Zealand", "Consumer Staples", "Food Products", "large", "NZD", "New Zealand dairy cooperative"),
    "SCL.NZ": Stock("SCL.NZ", "Scales Corporation Limited", "NZX", "New Zealand", "Consumer Staples", "Food Products", "mid", "NZD", "New Zealand food company"),
    "SML.NZ": Stock("SML.NZ", "Synlait Milk Limited", "NZX", "New Zealand", "Consumer Staples", "Food Products", "mid", "NZD", "New Zealand dairy processor"),
    "DGL.NZ": Stock("DGL.NZ", "Delegat Group Limited", "NZX", "New Zealand", "Consumer Staples", "Beverages", "mid", "NZD", "Wine producer and exporter"),
    
    # Consumer Discretionary
    "BGP.NZ": Stock("BGP.NZ", "Briscoe Group Limited", "NZX", "New Zealand", "Consumer Discretionary", "Retail", "large", "NZD", "New Zealand retail group"),
    "HLG.NZ": Stock("HLG.NZ", "Hallenstein Glasson Holdings Limited", "NZX", "New Zealand", "Consumer Discretionary", "Retail", "mid", "NZD", "New Zealand clothing retailer"),
    "KMD.NZ": Stock("KMD.NZ", "KMD Brands Limited", "NZX", "New Zealand", "Consumer Discretionary", "Retail", "mid", "NZD", "New Zealand retail brands company"),
    "WHS.NZ": Stock("WHS.NZ", "The Warehouse Group Limited", "NZX", "New Zealand", "Consumer Discretionary", "Retail", "mid", "NZD", "New Zealand retail group"),
    "RBD.NZ": Stock("RBD.NZ", "Restaurant Brands New Zealand Limited", "NZX", "New Zealand", "Consumer Discretionary", "Restaurants", "mid", "NZD", "Fast food restaurant operator"),
    "THL.NZ": Stock("THL.NZ", "Tourism Holdings Limited", "NZX", "New Zealand", "Consumer Discretionary", "Tourism", "mid", "NZD", "Tourism and RV rental company"),
    "MET.NZ": Stock("MET.NZ", "Me Today Limited", "NZX", "New Zealand", "Consumer Discretionary", "Personal Care", "small", "NZD", "Health and wellness products"),
    
    # New Zealand - Energy & Resources
    "GNE.NZ": Stock("GNE.NZ", "Genesis Energy Limited", "NZX", "New Zealand", "Utilities", "Electric Utilities", "large", "NZD", "New Zealand energy company"),
    "MEL.NZ": Stock("MEL.NZ", "Meridian Energy Limited", "NZX", "New Zealand", "Utilities", "Electric Utilities", "large", "NZD", "New Zealand renewable energy company"),
    "TPW.NZ": Stock("TPW.NZ", "Trustpower Limited", "NZX", "New Zealand", "Utilities", "Electric Utilities", "large", "NZD", "New Zealand electricity retailer"),
    "VCT.NZ": Stock("VCT.NZ", "Vector Limited", "NZX", "New Zealand", "Utilities", "Infrastructure", "large", "NZD", "New Zealand infrastructure company"),
    "CHI.NZ": Stock("CHI.NZ", "Channel Infrastructure NZ Limited", "NZX", "New Zealand", "Energy", "Oil & Gas", "mid", "NZD", "New Zealand infrastructure company"),
    
    # New Zealand - Materials & Construction
    "FBU.NZ": Stock("FBU.NZ", "Fletcher Building Limited", "NZX", "New Zealand", "Materials", "Building Materials", "large", "NZD", "New Zealand building materials company"),
    "STU.NZ": Stock("STU.NZ", "Steel & Tube Holdings Limited", "NZX", "New Zealand", "Materials", "Steel", "mid", "NZD", "New Zealand steel distributor"),
    "NZR.NZ": Stock("NZR.NZ", "New Zealand Refining Company Limited", "NZX", "New Zealand", "Materials", "Oil & Gas", "mid", "NZD", "Oil refining company"),
    "WIN.NZ": Stock("WIN.NZ", "Winton Land Limited", "NZX", "New Zealand", "Materials", "Real Estate Development", "mid", "NZD", "Property development company"),
    
    # New Zealand - Property & Infrastructure
    "GMT.NZ": Stock("GMT.NZ", "Goodman Property Trust", "NZX", "New Zealand", "Real Estate", "REITs", "large", "NZD", "New Zealand property investment company"),
    "KPG.NZ": Stock("KPG.NZ", "Kiwi Property Group Limited", "NZX", "New Zealand", "Real Estate", "REITs", "large", "NZD", "New Zealand property company"),
    "PCT.NZ": Stock("PCT.NZ", "Precinct Properties NZ", "NZX", "New Zealand", "Real Estate", "REITs", "large", "NZD", "New Zealand commercial property investor"),
    "PFI.NZ": Stock("PFI.NZ", "Property for Industry Limited", "NZX", "New Zealand", "Real Estate", "REITs", "large", "NZD", "New Zealand industrial property investor"),
    "VHP.NZ": Stock("VHP.NZ", "Vital Healthcare Property Trust", "NZX", "New Zealand", "Real Estate", "Healthcare REITs", "large", "NZD", "New Zealand healthcare property investor"),
    "IPL.NZ": Stock("IPL.NZ", "Investment Property Limited", "NZX", "New Zealand", "Real Estate", "REITs", "mid", "NZD", "Property investment company"),
    "NPT.NZ": Stock("NPT.NZ", "NPT Limited", "NZX", "New Zealand", "Real Estate", "REITs", "mid", "NZD", "Commercial property investor"),
    "SPG.NZ": Stock("SPG.NZ", "Stride Property Group", "NZX", "New Zealand", "Real Estate", "REITs", "large", "NZD", "Property investment and management"),
    
    # New Zealand - Industrials
    "AIR.NZ": Stock("AIR.NZ", "Air New Zealand Limited", "NZX", "New Zealand", "Industrials", "Airlines", "large", "NZD", "New Zealand flag carrier airline"),
    "AIA.NZ": Stock("AIA.NZ", "Auckland International Airport Limited", "NZX", "New Zealand", "Industrials", "Transportation", "large", "NZD", "New Zealand airport operator"),
    "FBU.NZ": Stock("FBU.NZ", "Fletcher Building Limited", "NZX", "New Zealand", "Industrials", "Building Materials", "large", "NZD", "New Zealand building materials company"),
    "POT.NZ": Stock("POT.NZ", "Port of Tauranga Limited", "NZX", "New Zealand", "Industrials", "Transportation", "large", "NZD", "New Zealand port operator"),
    "SKL.NZ": Stock("SKL.NZ", "Skellerup Holdings Limited", "NZX", "New Zealand", "Industrials", "Industrial Products", "mid", "NZD", "New Zealand industrial products manufacturer"),
    "FRW.NZ": Stock("FRW.NZ", "Freightways Group Limited", "NZX", "New Zealand", "Industrials", "Transportation", "large", "NZD", "New Zealand freight company"),
    "MOV.NZ": Stock("MOV.NZ", "Move Logistics Group Limited", "NZX", "New Zealand", "Industrials", "Transportation", "small", "NZD", "New Zealand logistics company"),
    "SPN.NZ": Stock("SPN.NZ", "South Port New Zealand Limited", "NZX", "New Zealand", "Industrials", "Transportation", "mid", "NZD", "New Zealand port operator"),
    "STU.NZ": Stock("STU.NZ", "Steel & Tube Holdings Limited", "NZX", "New Zealand", "Industrials", "Steel", "mid", "NZD", "New Zealand steel distributor"),
}
