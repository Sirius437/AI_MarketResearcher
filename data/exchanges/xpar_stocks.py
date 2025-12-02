"""
Euronext Paris (XPAR) - France stocks.
"""

from ..models import Stock

# France stocks
XPAR_STOCKS = {
    # France - Luxury Goods
    "MC.PA": Stock("MC.PA", "LVMH Moët Hennessy Louis Vuitton SE", "XPAR", "France", "Consumer Discretionary", "Luxury Goods", "large", "EUR", "French multinational luxury goods conglomerate"),
    "OR.PA": Stock("OR.PA", "L'Oréal S.A.", "XPAR", "France", "Consumer Staples", "Personal Care", "large", "EUR", "French personal care company"),
    
    # France - Healthcare
    "SAN.PA": Stock("SAN.PA", "Sanofi", "XPAR", "France", "Healthcare", "Pharmaceuticals", "large", "EUR", "French multinational pharmaceutical company"),
    
    # France - Energy
    "TTE.PA": Stock("TTE.PA", "TotalEnergies SE", "XPAR", "France", "Energy", "Oil & Gas", "large", "EUR", "French multinational integrated oil and gas company"),
    
    # France - Financials
    "BNP.PA": Stock("BNP.PA", "BNP Paribas", "XPAR", "France", "Financials", "Banking", "large", "EUR", "French international banking group"),
    "ACA.PA": Stock("ACA.PA", "Crédit Agricole S.A.", "XPAR", "France", "Financials", "Banking", "large", "EUR", "French network of cooperative and mutual banks"),
    
    # France - Industrials
    "AIR.PA": Stock("AIR.PA", "Airbus SE", "XPAR", "France", "Industrials", "Aerospace", "large", "EUR", "European multinational aerospace corporation"),
    "CAP.PA": Stock("CAP.PA", "Capgemini SE", "XPAR", "France", "Technology", "IT Services", "large", "EUR", "French multinational information technology services and consulting company"),
    
    # France - Utilities
    "EDF.PA": Stock("EDF.PA", "Électricité de France S.A.", "XPAR", "France", "Utilities", "Electric Utilities", "large", "EUR", "French electric utility company"),
    
    # France - Consumer Discretionary
    "RNO.PA": Stock("RNO.PA", "Renault S.A.", "XPAR", "France", "Consumer Discretionary", "Automotive", "large", "EUR", "French multinational automobile manufacturer"),
    "ML.PA": Stock("ML.PA", "Michelin", "XPAR", "France", "Consumer Discretionary", "Auto Parts", "large", "EUR", "French tire manufacturer"),
    
    # France - Materials
    "AI.PA": Stock("AI.PA", "Air Liquide S.A.", "XPAR", "France", "Materials", "Chemicals", "large", "EUR", "French multinational company supplying industrial gases"),
    
    # France - Technology
    "DSY.PA": Stock("DSY.PA", "Dassault Systèmes SE", "XPAR", "France", "Technology", "Software", "large", "EUR", "French software company"),
}
