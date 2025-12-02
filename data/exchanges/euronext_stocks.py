"""
Euronext (Paris, Amsterdam, Brussels, Lisbon) listed stocks.
"""

from ..models import Stock

EURONEXT_STOCKS = {
    # France (Paris)
    "ASML.AS": Stock("ASML.AS", "ASML Holding N.V.", "XAMS", "EU", "Technology", "Semiconductor Equipment", "large", "EUR", "Dutch multinational corporation that supplies photolithography systems"),
    "SAP.PA": Stock("SAP.PA", "SAP SE", "XPAR", "EU", "Technology", "Software", "large", "EUR", "German multinational software corporation"),
    "OR.PA": Stock("OR.PA", "L'Oréal S.A.", "XPAR", "EU", "Consumer Staples", "Personal Care", "large", "EUR", "French personal care company"),
    "MC.PA": Stock("MC.PA", "LVMH Moët Hennessy Louis Vuitton SE", "XPAR", "EU", "Consumer Discretionary", "Luxury Goods", "large", "EUR", "French multinational luxury goods conglomerate"),
    "SAN.PA": Stock("SAN.PA", "Sanofi S.A.", "XPAR", "EU", "Healthcare", "Pharmaceuticals", "large", "EUR", "French multinational pharmaceutical company"),
    "TTE.PA": Stock("TTE.PA", "TotalEnergies SE", "XPAR", "EU", "Energy", "Oil & Gas", "large", "EUR", "French multinational integrated energy and petroleum company"),
    "BNP.PA": Stock("BNP.PA", "BNP Paribas S.A.", "XPAR", "EU", "Financials", "Banking", "large", "EUR", "French international banking group"),
    "ACA.PA": Stock("ACA.PA", "Crédit Agricole S.A.", "XPAR", "EU", "Financials", "Banking", "large", "EUR", "French network of cooperative and mutual banks"),
    "SU.PA": Stock("SU.PA", "Schneider Electric SE", "XPAR", "EU", "Industrials", "Electrical Equipment", "large", "EUR", "French multinational corporation that specializes in energy management"),
    "AIR.PA": Stock("AIR.PA", "Airbus SE", "XPAR", "EU", "Industrials", "Aerospace", "large", "EUR", "European multinational aerospace corporation"),
    "VIV.PA": Stock("VIV.PA", "Vivendi SE", "XPAR", "EU", "Communication Services", "Media", "large", "EUR", "French mass media and telecommunications conglomerate"),
    "DSY.PA": Stock("DSY.PA", "Dassault Systèmes SE", "XPAR", "EU", "Technology", "Software", "large", "EUR", "French software corporation"),
    
    # Netherlands (Amsterdam)
    "RDSA.AS": Stock("RDSA.AS", "Royal Dutch Shell plc", "XAMS", "EU", "Energy", "Oil & Gas", "large", "EUR", "British-Dutch multinational oil and gas company"),
    "UNA.AS": Stock("UNA.AS", "Unilever N.V.", "XAMS", "EU", "Consumer Staples", "Personal Care", "large", "EUR", "Dutch-British multinational consumer goods company"),
    "INGA.AS": Stock("INGA.AS", "ING Groep N.V.", "XAMS", "EU", "Financials", "Banking", "large", "EUR", "Dutch multinational banking and financial services corporation"),
    "PHIA.AS": Stock("PHIA.AS", "Koninklijke Philips N.V.", "XAMS", "EU", "Healthcare", "Medical Technology", "large", "EUR", "Dutch multinational conglomerate corporation"),
    "HEIA.AS": Stock("HEIA.AS", "Heineken N.V.", "XAMS", "EU", "Consumer Staples", "Beverages", "large", "EUR", "Dutch multinational brewing company"),
    
    # Belgium (Brussels)
    "ABI.BR": Stock("ABI.BR", "Anheuser-Busch InBev SA/NV", "XBRU", "EU", "Consumer Staples", "Beverages", "large", "EUR", "Belgian multinational drink and brewing company"),
    "KBC.BR": Stock("KBC.BR", "KBC Group NV", "XBRU", "EU", "Financials", "Banking", "large", "EUR", "Belgian universal multi-channel bank-insurer"),
    
    # Portugal (Lisbon)
    "EDP.LS": Stock("EDP.LS", "EDP - Energias de Portugal, S.A.", "XLIS", "EU", "Utilities", "Electric Utilities", "large", "EUR", "Portuguese multinational energy corporation"),
    "GALP.LS": Stock("GALP.LS", "Galp Energia, SGPS, S.A.", "XLIS", "EU", "Energy", "Oil & Gas", "large", "EUR", "Portuguese multinational energy corporation"),
}
