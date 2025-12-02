"""
NASDAQ-listed stocks.
"""

from ..models import Stock

NASDAQ_STOCKS = {
    # Technology
    "AAPL": Stock("AAPL", "Apple Inc.", "NASDAQ", "US", "Technology", "Consumer Electronics", "large", "USD", "Designs and manufactures consumer electronics, software, and services"),
    "MSFT": Stock("MSFT", "Microsoft Corporation", "NASDAQ", "US", "Technology", "Software", "large", "USD", "Develops, licenses, and supports software, services, devices, and solutions"),
    "GOOGL": Stock("GOOGL", "Alphabet Inc.", "NASDAQ", "US", "Technology", "Internet Services", "large", "USD", "Provides online advertising services and cloud computing"),
    "AMZN": Stock("AMZN", "Amazon.com Inc.", "NASDAQ", "US", "Consumer Discretionary", "E-commerce", "large", "USD", "Online retailer and cloud computing services"),
    "TSLA": Stock("TSLA", "Tesla Inc.", "NASDAQ", "US", "Consumer Discretionary", "Electric Vehicles", "large", "USD", "Electric vehicle and clean energy company"),
    "NVDA": Stock("NVDA", "NVIDIA Corporation", "NASDAQ", "US", "Technology", "Semiconductors", "large", "USD", "Designs graphics processing units and system on chip units"),
    "META": Stock("META", "Meta Platforms Inc.", "NASDAQ", "US", "Technology", "Social Media", "large", "USD", "Social networking and virtual reality company"),
    "NFLX": Stock("NFLX", "Netflix Inc.", "NASDAQ", "US", "Communication Services", "Streaming", "large", "USD", "Streaming entertainment service"),
    "ADBE": Stock("ADBE", "Adobe Inc.", "NASDAQ", "US", "Technology", "Software", "large", "USD", "Computer software company"),
    "INTC": Stock("INTC", "Intel Corporation", "NASDAQ", "US", "Technology", "Semiconductors", "large", "USD", "Multinational corporation and technology company"),
    "AMD": Stock("AMD", "Advanced Micro Devices Inc.", "NASDAQ", "US", "Technology", "Semiconductors", "large", "USD", "Multinational semiconductor company"),
    "QCOM": Stock("QCOM", "QUALCOMM Incorporated", "NASDAQ", "US", "Technology", "Semiconductors", "large", "USD", "Multinational semiconductor and telecommunications equipment company"),
    "AVGO": Stock("AVGO", "Broadcom Inc.", "NASDAQ", "US", "Technology", "Semiconductors", "large", "USD", "Designer, developer and global supplier of semiconductor solutions"),
    "TXN": Stock("TXN", "Texas Instruments Incorporated", "NASDAQ", "US", "Technology", "Semiconductors", "large", "USD", "American technology company that designs and manufactures semiconductors"),
    "CSCO": Stock("CSCO", "Cisco Systems Inc.", "NASDAQ", "US", "Technology", "Networking", "large", "USD", "Multinational technology conglomerate"),
    "ROKU": Stock("ROKU", "Roku Inc.", "NASDAQ", "US", "Technology", "Streaming Devices", "mid", "USD", "American digital media player company"),
    "ZM": Stock("ZM", "Zoom Video Communications Inc.", "NASDAQ", "US", "Technology", "Video Communications", "mid", "USD", "American communications technology company"),
    "DOCU": Stock("DOCU", "DocuSign Inc.", "NASDAQ", "US", "Technology", "Software", "mid", "USD", "Electronic signature technology company"),
    "OKTA": Stock("OKTA", "Okta Inc.", "NASDAQ", "US", "Technology", "Cybersecurity", "mid", "USD", "Identity and access management company"),
    "CRWD": Stock("CRWD", "CrowdStrike Holdings Inc.", "NASDAQ", "US", "Technology", "Cybersecurity", "large", "USD", "Cybersecurity technology company"),
    "ZS": Stock("ZS", "Zscaler Inc.", "NASDAQ", "US", "Technology", "Cybersecurity", "mid", "USD", "Cloud security company"),
    
    # Financials
    "PYPL": Stock("PYPL", "PayPal Holdings Inc.", "NASDAQ", "US", "Financials", "Payment Processing", "large", "USD", "American multinational financial technology company"),
    "CME": Stock("CME", "CME Group Inc.", "NASDAQ", "US", "Financials", "Financial Markets", "large", "USD", "Financial markets company"),
    
    # Healthcare
    "AMGN": Stock("AMGN", "Amgen Inc.", "NASDAQ", "US", "Healthcare", "Biotechnology", "large", "USD", "American multinational biopharmaceutical company"),
    "GILD": Stock("GILD", "Gilead Sciences Inc.", "NASDAQ", "US", "Healthcare", "Biotechnology", "large", "USD", "American biopharmaceutical company"),
    "REGN": Stock("REGN", "Regeneron Pharmaceuticals Inc.", "NASDAQ", "US", "Healthcare", "Biotechnology", "large", "USD", "American biotechnology company"),
    "VRTX": Stock("VRTX", "Vertex Pharmaceuticals Incorporated", "NASDAQ", "US", "Healthcare", "Biotechnology", "large", "USD", "American biotechnology company"),
    "BIIB": Stock("BIIB", "Biogen Inc.", "NASDAQ", "US", "Healthcare", "Biotechnology", "large", "USD", "American multinational biotechnology company"),
    "ILMN": Stock("ILMN", "Illumina Inc.", "NASDAQ", "US", "Healthcare", "Life Sciences Tools", "large", "USD", "American biotechnology company"),
    "MRNA": Stock("MRNA", "Moderna Inc.", "NASDAQ", "US", "Healthcare", "Biotechnology", "large", "USD", "American biotechnology company"),
    
    # Consumer Discretionary
    "SBUX": Stock("SBUX", "Starbucks Corporation", "NASDAQ", "US", "Consumer Discretionary", "Restaurants", "large", "USD", "American multinational chain of coffeehouses"),
    "COST": Stock("COST", "Costco Wholesale Corporation", "NASDAQ", "US", "Consumer Staples", "Retail", "large", "USD", "American multinational corporation which operates membership-only warehouse clubs"),
    "BKNG": Stock("BKNG", "Booking Holdings Inc.", "NASDAQ", "US", "Consumer Discretionary", "Online Travel", "large", "USD", "American online travel agency"),
    "ABNB": Stock("ABNB", "Airbnb Inc.", "NASDAQ", "US", "Consumer Discretionary", "Home Sharing", "large", "USD", "American online marketplace for lodging"),
    "UBER": Stock("UBER", "Uber Technologies Inc.", "NASDAQ", "US", "Technology", "Ride Sharing", "large", "USD", "American multinational ride-hailing company"),
    "DASH": Stock("DASH", "DoorDash Inc.", "NASDAQ", "US", "Consumer Discretionary", "Food Delivery", "large", "USD", "American food delivery company"),
    
    # Communication Services
    "TMUS": Stock("TMUS", "T-Mobile US Inc.", "NASDAQ", "US", "Communication Services", "Telecommunications", "large", "USD", "American wireless network operator"),
    "CHTR": Stock("CHTR", "Charter Communications Inc.", "NASDAQ", "US", "Communication Services", "Cable", "large", "USD", "American telecommunications and mass media company"),
    
    # Industrials
    "PCAR": Stock("PCAR", "PACCAR Inc.", "NASDAQ", "US", "Industrials", "Trucks", "large", "USD", "American truck manufacturer"),
    "FAST": Stock("FAST", "Fastenal Company", "NASDAQ", "US", "Industrials", "Industrial Distribution", "large", "USD", "American industrial supply company"),
    
    # Materials
    "LRCX": Stock("LRCX", "Lam Research Corporation", "NASDAQ", "US", "Technology", "Semiconductor Equipment", "large", "USD", "American supplier of wafer fabrication equipment"),
    "AMAT": Stock("AMAT", "Applied Materials Inc.", "NASDAQ", "US", "Technology", "Semiconductor Equipment", "large", "USD", "American corporation that supplies equipment, services and software"),
    "KLAC": Stock("KLAC", "KLA Corporation", "NASDAQ", "US", "Technology", "Semiconductor Equipment", "large", "USD", "American capital equipment company"),
    
    # Energy
    "FANG": Stock("FANG", "Diamondback Energy Inc.", "NASDAQ", "US", "Energy", "Oil & Gas", "large", "USD", "American petroleum and natural gas exploration company"),
    
    # Utilities
    "AEP": Stock("AEP", "American Electric Power Company Inc.", "NASDAQ", "US", "Utilities", "Electric Utilities", "large", "USD", "American domestic electric utility company"),
    "EXC": Stock("EXC", "Exelon Corporation", "NASDAQ", "US", "Utilities", "Electric Utilities", "large", "USD", "American Fortune 100 energy company"),
    
    # Real Estate
    "PLD": Stock("PLD", "Prologis Inc.", "NASDAQ", "US", "Real Estate", "REITs", "large", "USD", "American real estate investment trust"),
}
