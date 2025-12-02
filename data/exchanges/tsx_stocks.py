"""
Toronto Stock Exchange (TSX) stocks.
"""

from ..models import Stock

# Toronto Stock Exchange stocks
TSX_STOCKS = {
    # Canada - Banks
    "RY.TO": Stock("RY.TO", "Royal Bank of Canada", "TSX", "Canada", "Financials", "Banking", "large", "CAD", "Canadian multinational financial services company"),
    "TD.TO": Stock("TD.TO", "Toronto-Dominion Bank", "TSX", "Canada", "Financials", "Banking", "large", "CAD", "Canadian multinational banking and financial services corporation"),
    "BNS.TO": Stock("BNS.TO", "Bank of Nova Scotia", "TSX", "Canada", "Financials", "Banking", "large", "CAD", "Canadian multinational banking and financial services company"),
    "BMO.TO": Stock("BMO.TO", "Bank of Montreal", "TSX", "Canada", "Financials", "Banking", "large", "CAD", "Canadian multinational investment bank and financial services company"),
    "CM.TO": Stock("CM.TO", "Canadian Imperial Bank of Commerce", "TSX", "Canada", "Financials", "Banking", "large", "CAD", "Canadian multinational banking and financial services corporation"),
    
    # Canada - Mining/Energy
    "SHOP.TO": Stock("SHOP.TO", "Shopify Inc.", "TSX", "Canada", "Technology", "E-commerce Platform", "large", "CAD", "Canadian multinational e-commerce company"),
    "CNQ.TO": Stock("CNQ.TO", "Canadian Natural Resources", "TSX", "Canada", "Energy", "Oil & Gas", "large", "CAD", "Canadian oil and natural gas exploration, development and production company"),
    "SU.TO": Stock("SU.TO", "Suncor Energy", "TSX", "Canada", "Energy", "Oil & Gas", "large", "CAD", "Canadian integrated energy company"),
    "ABX.TO": Stock("ABX.TO", "Barrick Gold Corporation", "TSX", "Canada", "Materials", "Mining", "large", "CAD", "Canadian mining company"),
    "NEM.TO": Stock("NEM.TO", "Newmont Corporation", "TSX", "Canada", "Materials", "Mining", "large", "CAD", "American gold mining company"),
    
    # Canada - Telecommunications
    "BCE.TO": Stock("BCE.TO", "BCE Inc.", "TSX", "Canada", "Communication Services", "Telecommunications", "large", "CAD", "Canadian telecommunications company"),
    "T.TO": Stock("T.TO", "TELUS Corporation", "TSX", "Canada", "Communication Services", "Telecommunications", "large", "CAD", "Canadian telecommunications company"),
    "RCI.B.TO": Stock("RCI.B.TO", "Rogers Communications", "TSX", "Canada", "Communication Services", "Telecommunications", "large", "CAD", "Canadian communications and media company"),
    
    # Canada - Railways
    "CNR.TO": Stock("CNR.TO", "Canadian National Railway", "TSX", "Canada", "Industrials", "Transportation", "large", "CAD", "Canadian Class I freight railway company"),
    "CP.TO": Stock("CP.TO", "Canadian Pacific Railway", "TSX", "Canada", "Industrials", "Transportation", "large", "CAD", "Canadian Class I freight railway company"),
    
    # Canada - Utilities
    "FTS.TO": Stock("FTS.TO", "Fortis Inc.", "TSX", "Canada", "Utilities", "Electric Utilities", "large", "CAD", "Canadian electric utility holding company"),
    
    # Canada - Consumer
    "L.TO": Stock("L.TO", "Loblaw Companies", "TSX", "Canada", "Consumer Staples", "Retail", "large", "CAD", "Canadian retail company"),
    "MG.TO": Stock("MG.TO", "Magna International", "TSX", "Canada", "Consumer Discretionary", "Auto Parts", "large", "CAD", "Canadian automotive parts manufacturer"),
}
