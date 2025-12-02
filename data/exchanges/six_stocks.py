"""
SIX Swiss Exchange - Switzerland stocks.
"""

from ..models import Stock

# Switzerland stocks
SIX_STOCKS = {
    # Switzerland - Consumer Staples
    "NESN.SW": Stock("NESN.SW", "Nestlé S.A.", "SIX", "Switzerland", "Consumer Staples", "Food Products", "large", "CHF", "Swiss multinational food and drink processing conglomerate"),
    
    # Switzerland - Healthcare
    "NOVN.SW": Stock("NOVN.SW", "Novartis AG", "SIX", "Switzerland", "Healthcare", "Pharmaceuticals", "large", "CHF", "Swiss multinational pharmaceutical company"),
    "ROG.SW": Stock("ROG.SW", "Roche Holding AG", "SIX", "Switzerland", "Healthcare", "Pharmaceuticals", "large", "CHF", "Swiss multinational healthcare company"),
    "LONN.SW": Stock("LONN.SW", "Lonza Group AG", "SIX", "Switzerland", "Healthcare", "Life Sciences", "large", "CHF", "Swiss chemicals and biotechnology company"),
    
    # Switzerland - Financials
    "UBS.SW": Stock("UBS.SW", "UBS Group AG", "SIX", "Switzerland", "Financials", "Investment Banking", "large", "CHF", "Swiss multinational investment bank and financial services company"),
    "CSGN.SW": Stock("CSGN.SW", "Credit Suisse Group AG", "SIX", "Switzerland", "Financials", "Investment Banking", "large", "CHF", "Swiss multinational investment bank"),
    "ZURN.SW": Stock("ZURN.SW", "Zurich Insurance Group AG", "SIX", "Switzerland", "Financials", "Insurance", "large", "CHF", "Swiss insurance company"),
    
    # Switzerland - Industrials
    "ABBN.SW": Stock("ABBN.SW", "ABB Ltd", "SIX", "Switzerland", "Industrials", "Industrial Automation", "large", "CHF", "Swiss-Swedish multinational corporation"),
    "GEBN.SW": Stock("GEBN.SW", "Geberit AG", "SIX", "Switzerland", "Industrials", "Construction", "large", "CHF", "Swiss multinational group specialized in sanitary products"),
    
    # Switzerland - Consumer Discretionary
    "CFR.SW": Stock("CFR.SW", "Compagnie Financière Richemont SA", "SIX", "Switzerland", "Consumer Discretionary", "Luxury Goods", "large", "CHF", "Swiss luxury goods holding company"),
    "SWTCH.SW": Stock("SWTCH.SW", "The Swatch Group AG", "SIX", "Switzerland", "Consumer Discretionary", "Luxury Goods", "large", "CHF", "Swiss manufacturer of watches"),
    
    # Switzerland - Technology
    "TEMN.SW": Stock("TEMN.SW", "Temenos AG", "SIX", "Switzerland", "Technology", "Software", "large", "CHF", "Swiss banking software company"),
    
    # Switzerland - Materials
    "LHN.SW": Stock("LHN.SW", "LafargeHolcim Ltd", "SIX", "Switzerland", "Materials", "Construction Materials", "large", "CHF", "Swiss multinational company that manufactures building materials"),
}
