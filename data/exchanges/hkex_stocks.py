"""
Hong Kong Stock Exchange (HKEX) stocks.
Comprehensive listing of major Hong Kong stocks across all sectors.
"""

from ..models import Stock

# Hong Kong Stock Exchange stocks
HKEX_STOCKS = {
    # Technology & Internet
    "0700.HK": Stock("0700.HK", "Tencent Holdings Limited", "HKEX", "Hong Kong", "Technology", "Internet Services", "large", "HKD", "Chinese multinational technology conglomerate"),
    "9988.HK": Stock("9988.HK", "Alibaba Group Holding Limited", "HKEX", "Hong Kong", "Technology", "E-commerce", "large", "HKD", "Chinese multinational technology company"),
    "3690.HK": Stock("3690.HK", "Meituan", "HKEX", "Hong Kong", "Technology", "Food Delivery", "large", "HKD", "Chinese technology company"),
    "1024.HK": Stock("1024.HK", "Kuaishou Technology", "HKEX", "Hong Kong", "Technology", "Social Media", "large", "HKD", "Chinese video sharing mobile app"),
    "2018.HK": Stock("2018.HK", "AAC Technologies Holdings", "HKEX", "Hong Kong", "Technology", "Consumer Electronics", "large", "HKD", "Provider of miniaturized technology solutions"),
    "1810.HK": Stock("1810.HK", "Xiaomi Corporation", "HKEX", "Hong Kong", "Technology", "Consumer Electronics", "large", "HKD", "Chinese electronics company"),
    "9618.HK": Stock("9618.HK", "JD.com Inc", "HKEX", "Hong Kong", "Technology", "E-commerce", "large", "HKD", "Chinese e-commerce company"),
    "9888.HK": Stock("9888.HK", "Baidu Inc", "HKEX", "Hong Kong", "Technology", "Internet Services", "large", "HKD", "Chinese multinational technology company"),
    "9999.HK": Stock("9999.HK", "NetEase Inc", "HKEX", "Hong Kong", "Technology", "Gaming", "large", "HKD", "Chinese internet technology company"),
    "1698.HK": Stock("1698.HK", "Tencent Music Entertainment Group", "HKEX", "Hong Kong", "Technology", "Music Streaming", "large", "HKD", "Chinese music streaming platform"),
    "2382.HK": Stock("2382.HK", "Sunny Optical Technology Group", "HKEX", "Hong Kong", "Technology", "Optical Components", "large", "HKD", "Optical and imaging products manufacturer"),
    
    # Banking & Finance
    "0005.HK": Stock("0005.HK", "HSBC Holdings plc", "HKEX", "Hong Kong", "Financials", "Banking", "large", "HKD", "British multinational investment bank"),
    "0011.HK": Stock("0011.HK", "Hang Seng Bank Limited", "HKEX", "Hong Kong", "Financials", "Banking", "large", "HKD", "Hong Kong-based banking and financial services company"),
    "0939.HK": Stock("0939.HK", "China Construction Bank Corporation", "HKEX", "Hong Kong", "Financials", "Banking", "large", "HKD", "Chinese state-owned commercial bank"),
    "3988.HK": Stock("3988.HK", "Bank of China Limited", "HKEX", "Hong Kong", "Financials", "Banking", "large", "HKD", "Chinese state-owned commercial bank"),
    "1398.HK": Stock("1398.HK", "Industrial and Commercial Bank of China", "HKEX", "Hong Kong", "Financials", "Banking", "large", "HKD", "Chinese multinational banking company"),
    "2388.HK": Stock("2388.HK", "BOC Hong Kong Holdings Limited", "HKEX", "Hong Kong", "Financials", "Banking", "large", "HKD", "Hong Kong-based commercial banking group"),
    "3968.HK": Stock("3968.HK", "China Merchants Bank Co Ltd", "HKEX", "Hong Kong", "Financials", "Banking", "large", "HKD", "Chinese commercial bank"),
    "6030.HK": Stock("6030.HK", "CITIC Securities Company Limited", "HKEX", "Hong Kong", "Financials", "Investment Banking", "large", "HKD", "Chinese investment bank and brokerage"),
    
    # Insurance
    "1299.HK": Stock("1299.HK", "AIA Group Limited", "HKEX", "Hong Kong", "Financials", "Insurance", "large", "HKD", "Pan-Asian life insurance group"),
    "2318.HK": Stock("2318.HK", "Ping An Insurance Group Company of China Ltd", "HKEX", "Hong Kong", "Financials", "Insurance", "large", "HKD", "Chinese insurance company"),
    "2628.HK": Stock("2628.HK", "China Life Insurance Company Limited", "HKEX", "Hong Kong", "Financials", "Insurance", "large", "HKD", "Chinese life insurance company"),
    "1336.HK": Stock("1336.HK", "New China Life Insurance Company Ltd", "HKEX", "Hong Kong", "Financials", "Insurance", "large", "HKD", "Chinese life insurance company"),
    
    # Real Estate & Property
    "0001.HK": Stock("0001.HK", "CK Hutchison Holdings Limited", "HKEX", "Hong Kong", "Industrials", "Conglomerate", "large", "HKD", "Hong Kong-based multinational conglomerate"),
    "0016.HK": Stock("0016.HK", "Sun Hung Kai Properties Limited", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Hong Kong property development company"),
    "0012.HK": Stock("0012.HK", "Henderson Land Development Company Limited", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Hong Kong property developer"),
    "0017.HK": Stock("0017.HK", "New World Development Company Limited", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Hong Kong property development company"),
    "0083.HK": Stock("0083.HK", "Sino Land Company Limited", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Hong Kong property development company"),
    "0101.HK": Stock("0101.HK", "Hang Lung Properties Limited", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Hong Kong property investment and development company"),
    "1109.HK": Stock("1109.HK", "China Resources Land Limited", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Chinese property development company"),
    "1997.HK": Stock("1997.HK", "Wharf Real Estate Investment Company Limited", "HKEX", "Hong Kong", "Real Estate", "REITs", "large", "HKD", "Hong Kong real estate investment company"),
    "0688.HK": Stock("0688.HK", "China Overseas Land & Investment Ltd", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Chinese property developer"),
    "3383.HK": Stock("3383.HK", "Agile Group Holdings Limited", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Chinese property developer"),
    
    # Utilities
    "0002.HK": Stock("0002.HK", "CLP Holdings Limited", "HKEX", "Hong Kong", "Utilities", "Electric Utilities", "large", "HKD", "Hong Kong-based power company"),
    "0003.HK": Stock("0003.HK", "The Hong Kong and China Gas Company Limited", "HKEX", "Hong Kong", "Utilities", "Gas Utilities", "large", "HKD", "Hong Kong gas company"),
    "0006.HK": Stock("0006.HK", "Power Assets Holdings Limited", "HKEX", "Hong Kong", "Utilities", "Electric Utilities", "large", "HKD", "Hong Kong electricity investment company"),
    
    # Consumer Goods & Retail
    "0288.HK": Stock("0288.HK", "WH Group Limited", "HKEX", "Hong Kong", "Consumer Staples", "Food Products", "large", "HKD", "Chinese meat and food processing company"),
    "1044.HK": Stock("1044.HK", "Hengan International Group Company Limited", "HKEX", "Hong Kong", "Consumer Staples", "Personal Care", "large", "HKD", "Chinese personal care and hygiene products company"),
    "0151.HK": Stock("0151.HK", "Want Want China Holdings Limited", "HKEX", "Hong Kong", "Consumer Staples", "Food Products", "large", "HKD", "Chinese food and beverage company"),
    "0291.HK": Stock("0291.HK", "China Resources Beer Holdings Company Limited", "HKEX", "Hong Kong", "Consumer Staples", "Beverages", "large", "HKD", "Chinese beer company"),
    "1898.HK": Stock("1898.HK", "China Coal Energy Company Limited", "HKEX", "Hong Kong", "Energy", "Coal", "large", "HKD", "Chinese coal mining company"),
    "0020.HK": Stock("0020.HK", "Sensetime Group Inc", "HKEX", "Hong Kong", "Technology", "Artificial Intelligence", "large", "HKD", "Chinese AI company"),
    
    # Healthcare & Pharmaceuticals
    "1093.HK": Stock("1093.HK", "CSPC Pharmaceutical Group Limited", "HKEX", "Hong Kong", "Healthcare", "Pharmaceuticals", "large", "HKD", "Chinese pharmaceutical company"),
    "1099.HK": Stock("1099.HK", "Sinopharm Group Co Ltd", "HKEX", "Hong Kong", "Healthcare", "Pharmaceuticals", "large", "HKD", "Chinese pharmaceutical company"),
    "2269.HK": Stock("2269.HK", "Wuxi Biologics Cayman Inc", "HKEX", "Hong Kong", "Healthcare", "Biotechnology", "large", "HKD", "Chinese biotechnology company"),
    "6185.HK": Stock("6185.HK", "Cansinobio", "HKEX", "Hong Kong", "Healthcare", "Biotechnology", "large", "HKD", "Chinese vaccine developer"),
    "1801.HK": Stock("1801.HK", "Innovation Pharmaceuticals Holdings Limited", "HKEX", "Hong Kong", "Healthcare", "Pharmaceuticals", "medium", "HKD", "Pharmaceutical company"),
    
    # Energy & Resources
    "0857.HK": Stock("0857.HK", "PetroChina Company Limited", "HKEX", "Hong Kong", "Energy", "Oil & Gas", "large", "HKD", "Chinese oil and gas company"),
    "0386.HK": Stock("0386.HK", "China Petroleum & Chemical Corporation", "HKEX", "Hong Kong", "Energy", "Oil & Gas", "large", "HKD", "Chinese petroleum and chemical company"),
    "0883.HK": Stock("0883.HK", "CNOOC Limited", "HKEX", "Hong Kong", "Energy", "Oil & Gas", "large", "HKD", "Chinese offshore oil company"),
    "1088.HK": Stock("1088.HK", "China Shenhua Energy Company Limited", "HKEX", "Hong Kong", "Energy", "Coal", "large", "HKD", "Chinese coal mining company"),
    "1171.HK": Stock("1171.HK", "Yankuang Energy Group Company Limited", "HKEX", "Hong Kong", "Energy", "Coal", "large", "HKD", "Chinese coal mining company"),
    
    # Transportation & Logistics
    "0066.HK": Stock("0066.HK", "MTR Corporation Limited", "HKEX", "Hong Kong", "Industrials", "Transportation", "large", "HKD", "Hong Kong railway operator"),
    "0293.HK": Stock("0293.HK", "Cathay Pacific Airways Limited", "HKEX", "Hong Kong", "Industrials", "Airlines", "large", "HKD", "Hong Kong-based airline"),
    "0019.HK": Stock("0019.HK", "Swire Pacific Limited", "HKEX", "Hong Kong", "Industrials", "Conglomerate", "large", "HKD", "Hong Kong-based conglomerate"),
    "0144.HK": Stock("0144.HK", "China Merchants Port Holdings Company Limited", "HKEX", "Hong Kong", "Industrials", "Marine Ports", "large", "HKD", "Chinese port operator"),
    
    # Telecommunications
    "0728.HK": Stock("0728.HK", "China Telecom Corporation Limited", "HKEX", "Hong Kong", "Telecommunications", "Telecom Services", "large", "HKD", "Chinese telecommunications company"),
    "0762.HK": Stock("0762.HK", "China Unicom Hong Kong Limited", "HKEX", "Hong Kong", "Telecommunications", "Telecom Services", "large", "HKD", "Chinese telecommunications company"),
    "0941.HK": Stock("0941.HK", "China Mobile Limited", "HKEX", "Hong Kong", "Telecommunications", "Telecom Services", "large", "HKD", "Chinese mobile telecommunications company"),
    
    # Materials & Manufacturing
    "0267.HK": Stock("0267.HK", "CITIC Limited", "HKEX", "Hong Kong", "Industrials", "Conglomerate", "large", "HKD", "Chinese state-owned conglomerate"),
    "0390.HK": Stock("0390.HK", "China Railway Group Limited", "HKEX", "Hong Kong", "Industrials", "Construction", "large", "HKD", "Chinese railway construction company"),
    "1186.HK": Stock("1186.HK", "China Rail Construction Corporation Limited", "HKEX", "Hong Kong", "Industrials", "Construction", "large", "HKD", "Chinese railway construction company"),
    "0914.HK": Stock("0914.HK", "Anhui Conch Cement Company Limited", "HKEX", "Hong Kong", "Materials", "Construction Materials", "large", "HKD", "Chinese cement manufacturer"),
    "2020.HK": Stock("2020.HK", "ANTA Sports Products Limited", "HKEX", "Hong Kong", "Consumer Discretionary", "Apparel", "large", "HKD", "Chinese sportswear company"),
    
    # Gaming & Entertainment
    "0027.HK": Stock("0027.HK", "Galaxy Entertainment Group Limited", "HKEX", "Hong Kong", "Consumer Discretionary", "Casinos & Gaming", "large", "HKD", "Macau casino operator"),
    "0200.HK": Stock("0200.HK", "Melco Resorts & Entertainment Limited", "HKEX", "Hong Kong", "Consumer Discretionary", "Casinos & Gaming", "large", "HKD", "Macau casino operator"),
    "1928.HK": Stock("1928.HK", "Sands China Ltd", "HKEX", "Hong Kong", "Consumer Discretionary", "Casinos & Gaming", "large", "HKD", "Macau casino operator"),
    "6808.HK": Stock("6808.HK", "SJM Holdings Limited", "HKEX", "Hong Kong", "Consumer Discretionary", "Casinos & Gaming", "large", "HKD", "Macau casino operator"),
    
    # Electric Vehicles & New Energy
    "1211.HK": Stock("1211.HK", "BYD Company Limited", "HKEX", "Hong Kong", "Consumer Discretionary", "Automobiles", "large", "HKD", "Chinese electric vehicle manufacturer"),
    "2015.HK": Stock("2015.HK", "Li Auto Inc", "HKEX", "Hong Kong", "Consumer Discretionary", "Automobiles", "large", "HKD", "Chinese electric vehicle manufacturer"),
    "9868.HK": Stock("9868.HK", "Xpeng Inc", "HKEX", "Hong Kong", "Consumer Discretionary", "Automobiles", "large", "HKD", "Chinese electric vehicle manufacturer"),
    "9866.HK": Stock("9866.HK", "NIO Inc", "HKEX", "Hong Kong", "Consumer Discretionary", "Automobiles", "large", "HKD", "Chinese electric vehicle manufacturer"),
    
    # Food & Beverage
    "0322.HK": Stock("0322.HK", "Tingyi Cayman Islands Holding Corp", "HKEX", "Hong Kong", "Consumer Staples", "Food Products", "large", "HKD", "Chinese food and beverage company"),
    "0345.HK": Stock("0345.HK", "Vitasoy International Holdings Ltd", "HKEX", "Hong Kong", "Consumer Staples", "Beverages", "medium", "HKD", "Hong Kong beverage company"),
    
    # Retail & E-commerce
    "0522.HK": Stock("0522.HK", "ASM Pacific Technology Limited", "HKEX", "Hong Kong", "Technology", "Semiconductors", "large", "HKD", "Semiconductor assembly and test equipment manufacturer"),
    "1972.HK": Stock("1972.HK", "Swireproperties Limited", "HKEX", "Hong Kong", "Real Estate", "Real Estate Development", "large", "HKD", "Hong Kong property company"),
}
