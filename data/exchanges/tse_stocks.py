"""
Tokyo Stock Exchange (TSE) listed stocks - Comprehensive listing of major Japanese companies.
Includes companies from TSEJ integration and major Japanese corporations across all sectors.
"""

from ..models import Stock

TSE_STOCKS = {
    # === AUTOMOTIVE & TRANSPORTATION ===
    "7203.T": Stock("7203.T", "Toyota Motor Corporation", "TSEJ", "Japan", "Consumer Discretionary", "Automotive", "large", "JPY", "World's largest automotive manufacturer by production"),
    "7267.T": Stock("7267.T", "Honda Motor Co., Ltd.", "TSEJ", "Japan", "Consumer Discretionary", "Automotive", "large", "JPY", "Japanese multinational automotive and motorcycle manufacturer"),
    "7201.T": Stock("7201.T", "Nissan Motor Co., Ltd.", "TSEJ", "Japan", "Consumer Discretionary", "Automotive", "large", "JPY", "Japanese multinational automobile manufacturer"),
    
    # === TECHNOLOGY & ELECTRONICS ===
    "6758.T": Stock("6758.T", "Sony Group Corporation", "TSEJ", "Japan", "Technology", "Consumer Electronics", "large", "JPY", "Japanese multinational conglomerate in electronics, gaming, and entertainment"),
    "6861.T": Stock("6861.T", "Keyence Corporation", "TSEJ", "Japan", "Technology", "Industrial Automation", "large", "JPY", "Leading manufacturer of automation sensors and measurement equipment"),
    "6954.T": Stock("6954.T", "Fanuc Corporation", "TSEJ", "Japan", "Industrials", "Industrial Automation", "large", "JPY", "World's largest maker of industrial robots and factory automation"),
    "6981.T": Stock("6981.T", "Murata Manufacturing Co., Ltd.", "TSEJ", "Japan", "Technology", "Electronic Components", "large", "JPY", "Leading manufacturer of electronic components and modules"),
    "8035.T": Stock("8035.T", "Tokyo Electron Limited", "TSEJ", "Japan", "Technology", "Semiconductor Equipment", "large", "JPY", "Major semiconductor and flat panel display production equipment manufacturer"),
    "7974.T": Stock("7974.T", "Nintendo Co., Ltd.", "TSEJ", "Japan", "Technology", "Gaming", "large", "JPY", "World's largest video game company by revenue"),
    
    # === TELECOMMUNICATIONS & INTERNET ===
    "9984.T": Stock("9984.T", "SoftBank Group Corp.", "TSEJ", "Japan", "Technology", "Investment", "large", "JPY", "Japanese multinational conglomerate and technology investment company"),
    "9432.T": Stock("9432.T", "Nippon Telegraph and Telephone Corporation", "TSEJ", "Japan", "Communication Services", "Telecommunications", "large", "JPY", "Japan's largest telecommunications company"),
    "9434.T": Stock("9434.T", "SoftBank Corp.", "TSEJ", "Japan", "Communication Services", "Telecommunications", "large", "JPY", "Major Japanese telecommunications operator"),
    "9433.T": Stock("9433.T", "KDDI Corporation", "TSEJ", "Japan", "Communication Services", "Telecommunications", "large", "JPY", "Japanese telecommunications operator"),
    
    # === FINANCIAL SERVICES ===
    "8306.T": Stock("8306.T", "Mitsubishi UFJ Financial Group, Inc.", "TSEJ", "Japan", "Financials", "Banking", "large", "JPY", "Japan's largest bank holding company"),
    "8316.T": Stock("8316.T", "Sumitomo Mitsui Financial Group, Inc.", "TSEJ", "Japan", "Financials", "Banking", "large", "JPY", "Major Japanese banking and financial services group"),
    "8411.T": Stock("8411.T", "Mizuho Financial Group, Inc.", "TSEJ", "Japan", "Financials", "Banking", "large", "JPY", "Japanese bank holding company"),
    
    # === HEALTHCARE & PHARMACEUTICALS ===
    "4519.T": Stock("4519.T", "Chugai Pharmaceutical Co., Ltd.", "TSEJ", "Japan", "Healthcare", "Pharmaceuticals", "large", "JPY", "Leading Japanese pharmaceutical company"),
    "4568.T": Stock("4568.T", "Daiichi Sankyo Company, Limited", "TSEJ", "Japan", "Healthcare", "Pharmaceuticals", "large", "JPY", "Major Japanese pharmaceutical company"),
    "4523.T": Stock("4523.T", "Eisai Co., Ltd.", "TSEJ", "Japan", "Healthcare", "Pharmaceuticals", "large", "JPY", "Japanese pharmaceutical company specializing in neurology and oncology"),
    
    # === MATERIALS & CHEMICALS ===
    "4063.T": Stock("4063.T", "Shin-Etsu Chemical Co., Ltd.", "TSEJ", "Japan", "Materials", "Chemicals", "large", "JPY", "Leading Japanese chemical company"),
    "4183.T": Stock("4183.T", "Mitsui Chemicals, Inc.", "TSEJ", "Japan", "Materials", "Chemicals", "large", "JPY", "Japanese chemical company"),
    "5020.T": Stock("5020.T", "ENEOS Holdings, Inc.", "TSEJ", "Japan", "Energy", "Oil & Gas", "large", "JPY", "Japan's largest oil refining company"),
    
    # === CONSUMER & RETAIL ===
    "9983.T": Stock("9983.T", "Fast Retailing Co., Ltd.", "TSEJ", "Japan", "Consumer Discretionary", "Apparel Retail", "large", "JPY", "Japanese retail holding company, operator of Uniqlo"),
    "2811.T": Stock("2811.T", "Kagome Co., Ltd.", "TSEJ", "Japan", "Consumer Staples", "Food Products", "mid", "JPY", "Japanese food processing company specializing in tomato-based products"),
    "2784.T": Stock("2784.T", "Alfresa Holdings Corp.", "TSEJ", "Japan", "Healthcare", "Healthcare Distribution", "large", "JPY", "Leading Japanese pharmaceutical wholesaler"),
    "2782.T": Stock("2782.T", "Seria Co., Ltd.", "TSEJ", "Japan", "Consumer Discretionary", "Retail", "mid", "JPY", "Japanese 100-yen discount store chain"),
    
    # === INDUSTRIALS & CONGLOMERATES ===
    "2768.T": Stock("2768.T", "Sojitz Corp.", "TSEJ", "Japan", "Industrials", "Trading Company", "large", "JPY", "Japanese general trading company (sogo shosha)"),
    "8031.T": Stock("8031.T", "Mitsui & Co., Ltd.", "TSEJ", "Japan", "Industrials", "Trading Company", "large", "JPY", "Japanese general trading company"),
    "8058.T": Stock("8058.T", "Mitsubishi Corporation", "TSEJ", "Japan", "Industrials", "Trading Company", "large", "JPY", "Japanese general trading company"),
    
    # === FOOD & BEVERAGES ===
    "1301.T": Stock("1301.T", "Kyokuyo Co., Ltd.", "TSEJ", "Japan", "Consumer Staples", "Food Processing", "mid", "JPY", "Japanese marine products and food processing company"),
    "2815.T": Stock("2815.T", "Ariake Japan Co., Ltd.", "TSEJ", "Japan", "Consumer Staples", "Food Products", "mid", "JPY", "Japanese natural seasoning manufacturer"),
    "2804.T": Stock("2804.T", "Bull-Dog Sauce Co., Ltd.", "TSEJ", "Japan", "Consumer Staples", "Food Products", "small", "JPY", "Japanese sauce and condiment manufacturer"),
    
    # === ETFs & INVESTMENT FUNDS ===
    "1305.T": Stock("1305.T", "iFree ETF-TOPIX", "TSEJ", "Japan", "Financials", "ETF", "large", "JPY", "ETF tracking the TOPIX index"),
    "1309.T": Stock("1309.T", "NF China SSE50 ETF", "TSEJ", "Japan", "Financials", "ETF", "mid", "JPY", "ETF tracking Chinese SSE 50 index"),
    "1311.T": Stock("1311.T", "NF TOPIX Core 30 ETF", "TSEJ", "Japan", "Financials", "ETF", "mid", "JPY", "ETF tracking TOPIX Core 30 index"),
    "1328.T": Stock("1328.T", "NF Gold Price ETF", "TSEJ", "Japan", "Financials", "ETF", "mid", "JPY", "Gold price tracking ETF"),
    
    # === REAL ESTATE & CONSTRUCTION ===
    "1332.T": Stock("1332.T", "Nissui Corp.", "TSEJ", "Japan", "Consumer Staples", "Food Processing", "large", "JPY", "Japanese fishery and marine products company"),
    "1379.T": Stock("1379.T", "Hokuto Corp.", "TSEJ", "Japan", "Consumer Staples", "Food Products", "mid", "JPY", "Japanese mushroom producer"),
    
    # === SPECIALTY COMPANIES ===
    "2764.T": Stock("2764.T", "Hiramatsu Inc.", "TSEJ", "Japan", "Consumer Discretionary", "Restaurants", "small", "JPY", "Japanese high-end restaurant operator"),
    "2769.T": Stock("2769.T", "Village Vanguard Co., Ltd.", "TSEJ", "Japan", "Consumer Discretionary", "Retail", "small", "JPY", "Japanese bookstore and entertainment goods retailer"),
    "2792.T": Stock("2792.T", "Honeys Holdings Co., Ltd.", "TSEJ", "Japan", "Consumer Discretionary", "Apparel", "small", "JPY", "Japanese women's clothing retailer"),
}
