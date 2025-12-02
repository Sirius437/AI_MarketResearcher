"""
NYSE-listed stocks.
"""

from ..models import Stock

NYSE_STOCKS = {
    # Technology
    "CRM": Stock("CRM", "Salesforce Inc.", "NYSE", "US", "Technology", "Software", "large", "USD", "Cloud-based software company"),
    "ORCL": Stock("ORCL", "Oracle Corporation", "NYSE", "US", "Technology", "Software", "large", "USD", "Computer technology corporation"),
    "IBM": Stock("IBM", "International Business Machines Corporation", "NYSE", "US", "Technology", "Software", "large", "USD", "Multinational technology corporation"),
    "SNOW": Stock("SNOW", "Snowflake Inc.", "NYSE", "US", "Technology", "Cloud Computing", "large", "USD", "American cloud computing company"),
    "PLTR": Stock("PLTR", "Palantir Technologies Inc.", "NYSE", "US", "Technology", "Data Analytics", "mid", "USD", "American software company specializing in big data analytics"),
    "TWLO": Stock("TWLO", "Twilio Inc.", "NYSE", "US", "Technology", "Cloud Communications", "mid", "USD", "Cloud communications platform"),
    "NET": Stock("NET", "Cloudflare Inc.", "NYSE", "US", "Technology", "Cloud Infrastructure", "mid", "USD", "Web infrastructure and website security company"),
    
    # Financials
    "JPM": Stock("JPM", "JPMorgan Chase & Co.", "NYSE", "US", "Financials", "Banking", "large", "USD", "Multinational investment bank and financial services company"),
    "BAC": Stock("BAC", "Bank of America Corporation", "NYSE", "US", "Financials", "Banking", "large", "USD", "Multinational investment bank and financial services company"),
    "WFC": Stock("WFC", "Wells Fargo & Company", "NYSE", "US", "Financials", "Banking", "large", "USD", "Multinational financial services company"),
    "GS": Stock("GS", "The Goldman Sachs Group Inc.", "NYSE", "US", "Financials", "Investment Banking", "large", "USD", "Multinational investment bank and financial services company"),
    "MS": Stock("MS", "Morgan Stanley", "NYSE", "US", "Financials", "Investment Banking", "large", "USD", "Multinational investment bank and financial services company"),
    "V": Stock("V", "Visa Inc.", "NYSE", "US", "Financials", "Payment Processing", "large", "USD", "Multinational financial services corporation"),
    "MA": Stock("MA", "Mastercard Incorporated", "NYSE", "US", "Financials", "Payment Processing", "large", "USD", "Multinational financial services corporation"),
    "C": Stock("C", "Citigroup Inc.", "NYSE", "US", "Financials", "Banking", "large", "USD", "Multinational investment bank and financial services corporation"),
    "AXP": Stock("AXP", "American Express Company", "NYSE", "US", "Financials", "Financial Services", "large", "USD", "Multinational financial services corporation"),
    "BLK": Stock("BLK", "BlackRock Inc.", "NYSE", "US", "Financials", "Asset Management", "large", "USD", "Multinational investment management corporation"),
    "SCHW": Stock("SCHW", "The Charles Schwab Corporation", "NYSE", "US", "Financials", "Brokerage", "large", "USD", "Bank and stock brokerage firm"),
    "ICE": Stock("ICE", "Intercontinental Exchange Inc.", "NYSE", "US", "Financials", "Financial Markets", "large", "USD", "American company that owns exchanges for financial and commodity markets"),
    "SPGI": Stock("SPGI", "S&P Global Inc.", "NYSE", "US", "Financials", "Financial Information", "large", "USD", "American publicly traded corporation"),
    "MCO": Stock("MCO", "Moody's Corporation", "NYSE", "US", "Financials", "Credit Rating", "large", "USD", "American business and financial services company"),
    
    # Healthcare
    "JNJ": Stock("JNJ", "Johnson & Johnson", "NYSE", "US", "Healthcare", "Pharmaceuticals", "large", "USD", "Multinational pharmaceutical, medical device, and consumer goods company"),
    "PFE": Stock("PFE", "Pfizer Inc.", "NYSE", "US", "Healthcare", "Pharmaceuticals", "large", "USD", "Multinational pharmaceutical and biotechnology corporation"),
    "UNH": Stock("UNH", "UnitedHealth Group Incorporated", "NYSE", "US", "Healthcare", "Health Insurance", "large", "USD", "Diversified health care company"),
    "ABBV": Stock("ABBV", "AbbVie Inc.", "NYSE", "US", "Healthcare", "Pharmaceuticals", "large", "USD", "Pharmaceutical company focused on immunology and oncology"),
    "MRK": Stock("MRK", "Merck & Co. Inc.", "NYSE", "US", "Healthcare", "Pharmaceuticals", "large", "USD", "American multinational pharmaceutical company"),
    "TMO": Stock("TMO", "Thermo Fisher Scientific Inc.", "NYSE", "US", "Healthcare", "Life Sciences", "large", "USD", "American biotechnology product development company"),
    "ABT": Stock("ABT", "Abbott Laboratories", "NYSE", "US", "Healthcare", "Medical Devices", "large", "USD", "American multinational medical devices and health care company"),
    "LLY": Stock("LLY", "Eli Lilly and Company", "NYSE", "US", "Healthcare", "Pharmaceuticals", "large", "USD", "American pharmaceutical company"),
    "BMY": Stock("BMY", "Bristol Myers Squibb Company", "NYSE", "US", "Healthcare", "Pharmaceuticals", "large", "USD", "American multinational pharmaceutical company"),
    "CVS": Stock("CVS", "CVS Health Corporation", "NYSE", "US", "Healthcare", "Healthcare Services", "large", "USD", "American healthcare company"),
    "ANTM": Stock("ANTM", "Anthem Inc.", "NYSE", "US", "Healthcare", "Health Insurance", "large", "USD", "American health insurance company"),
    "CI": Stock("CI", "Cigna Corporation", "NYSE", "US", "Healthcare", "Health Insurance", "large", "USD", "American multinational managed healthcare company"),
    "HUM": Stock("HUM", "Humana Inc.", "NYSE", "US", "Healthcare", "Health Insurance", "large", "USD", "American health insurance company"),
    
    # Energy
    "XOM": Stock("XOM", "Exxon Mobil Corporation", "NYSE", "US", "Energy", "Oil & Gas", "large", "USD", "Multinational oil and gas corporation"),
    "CVX": Stock("CVX", "Chevron Corporation", "NYSE", "US", "Energy", "Oil & Gas", "large", "USD", "Multinational energy corporation"),
    "COP": Stock("COP", "ConocoPhillips", "NYSE", "US", "Energy", "Oil & Gas", "large", "USD", "Multinational energy corporation"),
    "EOG": Stock("EOG", "EOG Resources Inc.", "NYSE", "US", "Energy", "Oil & Gas", "large", "USD", "American crude oil and natural gas exploration company"),
    "SLB": Stock("SLB", "Schlumberger Limited", "NYSE", "US", "Energy", "Oil & Gas Services", "large", "USD", "American oilfield services company"),
    "PSX": Stock("PSX", "Phillips 66", "NYSE", "US", "Energy", "Oil Refining", "large", "USD", "American multinational energy company"),
    "VLO": Stock("VLO", "Valero Energy Corporation", "NYSE", "US", "Energy", "Oil Refining", "large", "USD", "American multinational manufacturing company"),
    "MPC": Stock("MPC", "Marathon Petroleum Corporation", "NYSE", "US", "Energy", "Oil Refining", "large", "USD", "American petroleum refining company"),
    "KMI": Stock("KMI", "Kinder Morgan Inc.", "NYSE", "US", "Energy", "Pipeline", "large", "USD", "American energy infrastructure company"),
    "OKE": Stock("OKE", "ONEOK Inc.", "NYSE", "US", "Energy", "Pipeline", "large", "USD", "American diversified corporation"),
    "WMB": Stock("WMB", "The Williams Companies Inc.", "NYSE", "US", "Energy", "Pipeline", "large", "USD", "American energy company"),
    
    # Consumer Discretionary
    "HD": Stock("HD", "The Home Depot Inc.", "NYSE", "US", "Consumer Discretionary", "Home Improvement", "large", "USD", "American home improvement retail corporation"),
    "MCD": Stock("MCD", "McDonald's Corporation", "NYSE", "US", "Consumer Discretionary", "Restaurants", "large", "USD", "American fast food company"),
    "NKE": Stock("NKE", "NIKE Inc.", "NYSE", "US", "Consumer Discretionary", "Apparel", "large", "USD", "American multinational corporation engaged in the design, development, manufacturing, and marketing of footwear"),
    "LOW": Stock("LOW", "Lowe's Companies Inc.", "NYSE", "US", "Consumer Discretionary", "Home Improvement", "large", "USD", "American retail company specializing in home improvement"),
    "TJX": Stock("TJX", "The TJX Companies Inc.", "NYSE", "US", "Consumer Discretionary", "Apparel Retail", "large", "USD", "American multinational off-price department store corporation"),
    "F": Stock("F", "Ford Motor Company", "NYSE", "US", "Consumer Discretionary", "Automotive", "large", "USD", "American multinational automobile manufacturer"),
    "GM": Stock("GM", "General Motors Company", "NYSE", "US", "Consumer Discretionary", "Automotive", "large", "USD", "American multinational automotive manufacturing company"),
    
    # Consumer Staples
    "WMT": Stock("WMT", "Walmart Inc.", "NYSE", "US", "Consumer Staples", "Retail", "large", "USD", "American multinational retail corporation"),
    "PG": Stock("PG", "The Procter & Gamble Company", "NYSE", "US", "Consumer Staples", "Personal Care", "large", "USD", "American multinational consumer goods corporation"),
    "KO": Stock("KO", "The Coca-Cola Company", "NYSE", "US", "Consumer Staples", "Beverages", "large", "USD", "American multinational beverage corporation"),
    "PEP": Stock("PEP", "PepsiCo Inc.", "NYSE", "US", "Consumer Staples", "Food & Beverages", "large", "USD", "American multinational food, snack, and beverage corporation"),
    "WBA": Stock("WBA", "Walgreens Boots Alliance Inc.", "NYSE", "US", "Consumer Staples", "Pharmacy", "large", "USD", "American company that operates as the second-largest pharmacy store chain"),
    "KR": Stock("KR", "The Kroger Co.", "NYSE", "US", "Consumer Staples", "Grocery", "large", "USD", "American retail company founded by Bernard Kroger"),
    "CL": Stock("CL", "Colgate-Palmolive Company", "NYSE", "US", "Consumer Staples", "Personal Care", "large", "USD", "American multinational consumer products company"),
    "KMB": Stock("KMB", "Kimberly-Clark Corporation", "NYSE", "US", "Consumer Staples", "Personal Care", "large", "USD", "American multinational personal care corporation"),
    "GIS": Stock("GIS", "General Mills Inc.", "NYSE", "US", "Consumer Staples", "Food Products", "large", "USD", "American multinational manufacturer and marketer of branded consumer foods"),
    "K": Stock("K", "Kellogg Company", "NYSE", "US", "Consumer Staples", "Food Products", "large", "USD", "American multinational food manufacturing company"),
    
    # Communication Services
    "T": Stock("T", "AT&T Inc.", "NYSE", "US", "Communication Services", "Telecommunications", "large", "USD", "American multinational telecommunications holding company"),
    "VZ": Stock("VZ", "Verizon Communications Inc.", "NYSE", "US", "Communication Services", "Telecommunications", "large", "USD", "American multinational telecommunications conglomerate"),
    "DIS": Stock("DIS", "The Walt Disney Company", "NYSE", "US", "Communication Services", "Entertainment", "large", "USD", "American multinational mass media and entertainment conglomerate"),
    "CMCSA": Stock("CMCSA", "Comcast Corporation", "NYSE", "US", "Communication Services", "Cable", "large", "USD", "American telecommunications conglomerate"),
    
    # Industrials
    "BA": Stock("BA", "The Boeing Company", "NYSE", "US", "Industrials", "Aerospace", "large", "USD", "American multinational corporation that designs, manufactures, and sells airplanes"),
    "CAT": Stock("CAT", "Caterpillar Inc.", "NYSE", "US", "Industrials", "Construction Equipment", "large", "USD", "American Fortune 100 corporation that designs, develops, engineers, manufactures, markets, and sells machinery"),
    "GE": Stock("GE", "General Electric Company", "NYSE", "US", "Industrials", "Conglomerate", "large", "USD", "American multinational conglomerate"),
    "MMM": Stock("MMM", "3M Company", "NYSE", "US", "Industrials", "Conglomerate", "large", "USD", "American multinational conglomerate corporation"),
    "HON": Stock("HON", "Honeywell International Inc.", "NYSE", "US", "Industrials", "Conglomerate", "large", "USD", "American publicly traded, multinational conglomerate corporation"),
    "UPS": Stock("UPS", "United Parcel Service Inc.", "NYSE", "US", "Industrials", "Logistics", "large", "USD", "American multinational shipping & receiving and supply chain management company"),
    "FDX": Stock("FDX", "FedEx Corporation", "NYSE", "US", "Industrials", "Logistics", "large", "USD", "American multinational delivery services company"),
    "LMT": Stock("LMT", "Lockheed Martin Corporation", "NYSE", "US", "Industrials", "Aerospace & Defense", "large", "USD", "American aerospace, arms, defense, information security, and technology corporation"),
    "RTX": Stock("RTX", "Raytheon Technologies Corporation", "NYSE", "US", "Industrials", "Aerospace & Defense", "large", "USD", "American multinational aerospace and defense conglomerate"),
    "NOC": Stock("NOC", "Northrop Grumman Corporation", "NYSE", "US", "Industrials", "Aerospace & Defense", "large", "USD", "American multinational aerospace and defense technology company"),
    
    # Materials
    "LIN": Stock("LIN", "Linde plc", "NYSE", "US", "Materials", "Chemicals", "large", "USD", "Irish multinational chemical company"),
    "APD": Stock("APD", "Air Products and Chemicals Inc.", "NYSE", "US", "Materials", "Chemicals", "large", "USD", "American international corporation whose principal business is selling gases and chemicals"),
    "SHW": Stock("SHW", "The Sherwin-Williams Company", "NYSE", "US", "Materials", "Chemicals", "large", "USD", "American Fortune 500 company in the general building materials industry"),
    "FCX": Stock("FCX", "Freeport-McMoRan Inc.", "NYSE", "US", "Materials", "Mining", "large", "USD", "American mining company based in Phoenix, Arizona"),
    "NEM": Stock("NEM", "Newmont Corporation", "NYSE", "US", "Materials", "Mining", "large", "USD", "American gold mining company"),
    "DOW": Stock("DOW", "Dow Inc.", "NYSE", "US", "Materials", "Chemicals", "large", "USD", "American multinational chemical corporation"),
    
    # Utilities
    "NEE": Stock("NEE", "NextEra Energy Inc.", "NYSE", "US", "Utilities", "Electric Utilities", "large", "USD", "American energy company with about 58,000 megawatts of generating capacity"),
    "DUK": Stock("DUK", "Duke Energy Corporation", "NYSE", "US", "Utilities", "Electric Utilities", "large", "USD", "American electric power and natural gas holding company"),
    "SO": Stock("SO", "The Southern Company", "NYSE", "US", "Utilities", "Electric Utilities", "large", "USD", "American gas and electric utility holding company"),
    "D": Stock("D", "Dominion Energy Inc.", "NYSE", "US", "Utilities", "Electric Utilities", "large", "USD", "American power and gas company"),
    
    # Real Estate
    "AMT": Stock("AMT", "American Tower Corporation", "NYSE", "US", "Real Estate", "REITs", "large", "USD", "American real estate investment trust and an owner and operator of wireless and broadcast communications infrastructure"),
    "CCI": Stock("CCI", "Crown Castle International Corp.", "NYSE", "US", "Real Estate", "REITs", "large", "USD", "American real estate investment trust that owns, operates and leases more than 40,000 cell towers"),
    "EQIX": Stock("EQIX", "Equinix Inc.", "NYSE", "US", "Real Estate", "REITs", "large", "USD", "American multinational company headquartered in Redwood City, California"),
    "SPG": Stock("SPG", "Simon Property Group Inc.", "NYSE", "US", "Real Estate", "REITs", "large", "USD", "American real estate investment trust engaged in the ownership of shopping malls"),
}
