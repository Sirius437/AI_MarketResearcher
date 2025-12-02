"""
Borsa Italiana (MIL) - Italy stocks.
"""

from ..models import Stock

# Italy stocks
MIL_STOCKS = {
    # Italy - Energy
    "ENI.MI": Stock("ENI.MI", "Eni S.p.A.", "MIL", "Italy", "Energy", "Oil & Gas", "large", "EUR", "Italian multinational oil and gas company"),
    
    # Italy - Utilities
    "ENEL.MI": Stock("ENEL.MI", "Enel S.p.A.", "MIL", "Italy", "Utilities", "Electric Utilities", "large", "EUR", "Italian multinational manufacturer and distributor of electricity and gas"),
    
    # Italy - Financials
    "ISP.MI": Stock("ISP.MI", "Intesa Sanpaolo", "MIL", "Italy", "Financials", "Banking", "large", "EUR", "Italian banking group"),
    "UCG.MI": Stock("UCG.MI", "UniCredit S.p.A.", "MIL", "Italy", "Financials", "Banking", "large", "EUR", "Italian global banking and financial services company"),
    
    # Italy - Automotive
    "STLA.MI": Stock("STLA.MI", "Stellantis N.V.", "MIL", "Italy", "Consumer Discretionary", "Automotive", "large", "EUR", "Multinational automotive manufacturing corporation"),
    "RACE.MI": Stock("RACE.MI", "Ferrari N.V.", "MIL", "Italy", "Consumer Discretionary", "Automotive", "large", "EUR", "Italian luxury sports car manufacturer"),
    
    # Italy - Industrials
    "LDO.MI": Stock("LDO.MI", "Leonardo S.p.A.", "MIL", "Italy", "Industrials", "Aerospace", "large", "EUR", "Italian multinational aerospace company"),
    "ATL.MI": Stock("ATL.MI", "Atlantia S.p.A.", "MIL", "Italy", "Industrials", "Infrastructure", "large", "EUR", "Italian infrastructure company"),
    
    # Italy - Technology
    "STM.MI": Stock("STM.MI", "STMicroelectronics N.V.", "MIL", "Italy", "Technology", "Semiconductors", "large", "EUR", "European multinational electronics and semiconductor manufacturer"),
    
    # Italy - Consumer Staples
    "CPR.MI": Stock("CPR.MI", "Campari Group", "MIL", "Italy", "Consumer Staples", "Beverages", "large", "EUR", "Italian alcoholic beverages company"),
    
    # Italy - Telecommunications
    "TIT.MI": Stock("TIT.MI", "Telecom Italia S.p.A.", "MIL", "Italy", "Communication Services", "Telecommunications", "large", "EUR", "Italian telecommunications company"),
    
    # Italy - Materials
    "TERN.MI": Stock("TERN.MI", "Terna S.p.A.", "MIL", "Italy", "Utilities", "Electric Utilities", "large", "EUR", "Italian electricity transmission system operator"),
}
