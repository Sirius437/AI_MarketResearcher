"""
Stock Exchange of Thailand (SET) stocks.
"""

from ..models import Stock

# Thailand stocks
SET_STOCKS = {
    # Thailand - Banking
    "BBL.BK": Stock("BBL.BK", "Bangkok Bank Public Company Limited", "SET", "Thailand", "Financials", "Banking", "large", "THB", "Thai commercial bank"),
    "KBANK.BK": Stock("KBANK.BK", "Kasikornbank Public Company Limited", "SET", "Thailand", "Financials", "Banking", "large", "THB", "Thai commercial bank"),
    "SCB.BK": Stock("SCB.BK", "Siam Commercial Bank Public Company Limited", "SET", "Thailand", "Financials", "Banking", "large", "THB", "Thai commercial bank"),
    "KTB.BK": Stock("KTB.BK", "Krung Thai Bank Public Company Limited", "SET", "Thailand", "Financials", "Banking", "large", "THB", "Thai state-owned bank"),
    
    # Thailand - Energy
    "PTT.BK": Stock("PTT.BK", "PTT Public Company Limited", "SET", "Thailand", "Energy", "Oil & Gas", "large", "THB", "Thai state-owned oil and gas company"),
    "PTTEP.BK": Stock("PTTEP.BK", "PTT Exploration and Production Public Company Limited", "SET", "Thailand", "Energy", "Oil & Gas", "large", "THB", "Thai oil and gas exploration company"),
    "PTTGC.BK": Stock("PTTGC.BK", "PTT Global Chemical Public Company Limited", "SET", "Thailand", "Materials", "Chemicals", "large", "THB", "Thai petrochemical company"),
    "BANPU.BK": Stock("BANPU.BK", "Banpu Public Company Limited", "SET", "Thailand", "Energy", "Coal Mining", "large", "THB", "Thai energy company"),
    
    # Thailand - Telecommunications
    "ADVANC.BK": Stock("ADVANC.BK", "Advanced Info Service Public Company Limited", "SET", "Thailand", "Communication Services", "Telecommunications", "large", "THB", "Thai mobile telecommunications company"),
    "TRUE.BK": Stock("TRUE.BK", "True Corporation Public Company Limited", "SET", "Thailand", "Communication Services", "Telecommunications", "large", "THB", "Thai telecommunications company"),
    "DTAC.BK": Stock("DTAC.BK", "Total Access Communication Public Company Limited", "SET", "Thailand", "Communication Services", "Telecommunications", "large", "THB", "Thai mobile telecommunications company"),
    
    # Thailand - Consumer Goods
    "CP.BK": Stock("CP.BK", "Charoen Pokphand Foods Public Company Limited", "SET", "Thailand", "Consumer Staples", "Food Products", "large", "THB", "Thai agribusiness and food company"),
    "CPALL.BK": Stock("CPALL.BK", "CP ALL Public Company Limited", "SET", "Thailand", "Consumer Staples", "Retail", "large", "THB", "Thai convenience store operator"),
    "CBG.BK": Stock("CBG.BK", "Carabao Group Public Company Limited", "SET", "Thailand", "Consumer Staples", "Beverages", "large", "THB", "Thai energy drink company"),
    
    # Thailand - Real Estate
    "LPN.BK": Stock("LPN.BK", "LPN Development Public Company Limited", "SET", "Thailand", "Real Estate", "Real Estate Development", "large", "THB", "Thai property developer"),
    "AP.BK": Stock("AP.BK", "AP (Thailand) Public Company Limited", "SET", "Thailand", "Real Estate", "Real Estate Development", "large", "THB", "Thai property developer"),
    
    # Thailand - Industrials
    "SCC.BK": Stock("SCC.BK", "The Siam Cement Public Company Limited", "SET", "Thailand", "Materials", "Construction Materials", "large", "THB", "Thai cement and building materials company"),
    "SCGP.BK": Stock("SCGP.BK", "SCG Packaging Public Company Limited", "SET", "Thailand", "Materials", "Packaging", "large", "THB", "Thai packaging company"),
    
    # Thailand - Airlines
    "AOT.BK": Stock("AOT.BK", "Airports of Thailand Public Company Limited", "SET", "Thailand", "Industrials", "Transportation", "large", "THB", "Thai airport operator"),
    "THAI.BK": Stock("THAI.BK", "Thai Airways International Public Company Limited", "SET", "Thailand", "Industrials", "Airlines", "large", "THB", "Thai national airline"),
    
    # Thailand - Technology
    "GULF.BK": Stock("GULF.BK", "Gulf Energy Development Public Company Limited", "SET", "Thailand", "Utilities", "Electric Utilities", "large", "THB", "Thai power generation company"),
}
