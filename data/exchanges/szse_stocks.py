"""
Shenzhen Stock Exchange (SZSE) stocks - Comprehensive listing including ChiNext Growth Enterprise Market.
Includes main board (000xxx, 002xxx) and ChiNext (300xxx) stocks.
"""

from ..models import Stock

# Shenzhen Stock Exchange stocks - Expanded comprehensive listing
SZSE_STOCKS = {
    # === MAIN BOARD STOCKS ===
    # Banking & Financial Services
    "000001.SZ": Stock("000001.SZ", "Ping An Bank Co., Ltd.", "SZSE", "China", "Financials", "Banking", "large", "CNY", "Leading Chinese joint-stock commercial bank"),
    "000776.SZ": Stock("000776.SZ", "Guangfa Securities Co., Ltd.", "SZSE", "China", "Financials", "Securities", "large", "CNY", "Major Chinese securities company"),
    
    # Real Estate & Development
    "000002.SZ": Stock("000002.SZ", "China Vanke Co., Ltd.", "SZSE", "China", "Real Estate", "Real Estate Development", "large", "CNY", "Leading Chinese real estate developer"),
    "000069.SZ": Stock("000069.SZ", "Huafa Industrial Co., Ltd.", "SZSE", "China", "Real Estate", "Real Estate Development", "large", "CNY", "Chinese real estate and industrial company"),
    
    # Consumer Staples & Beverages
    "000858.SZ": Stock("000858.SZ", "Wuliangye Yibin Co., Ltd.", "SZSE", "China", "Consumer Staples", "Beverages", "large", "CNY", "Premium Chinese liquor producer"),
    "000596.SZ": Stock("000596.SZ", "Gujing Gongjiu Co., Ltd.", "SZSE", "China", "Consumer Staples", "Beverages", "large", "CNY", "Chinese alcoholic beverage company"),
    
    # Healthcare & Biotechnology
    "000661.SZ": Stock("000661.SZ", "Changchun High & New Technology Industries Group Inc.", "SZSE", "China", "Healthcare", "Biotechnology", "large", "CNY", "Chinese biotechnology and vaccine company"),
    "000963.SZ": Stock("000963.SZ", "Huadong Medicine Co., Ltd.", "SZSE", "China", "Healthcare", "Pharmaceuticals", "large", "CNY", "Chinese pharmaceutical company"),
    
    # Technology & Electronics
    "002415.SZ": Stock("002415.SZ", "Hangzhou Hikvision Digital Technology Co., Ltd.", "SZSE", "China", "Technology", "Security Equipment", "large", "CNY", "World's largest video surveillance equipment manufacturer"),
    "002230.SZ": Stock("002230.SZ", "Iflytek Co., Ltd.", "SZSE", "China", "Technology", "Artificial Intelligence", "large", "CNY", "Chinese AI and speech recognition technology company"),
    "002475.SZ": Stock("002475.SZ", "Luxshare Precision Industry Co., Ltd.", "SZSE", "China", "Technology", "Electronics Manufacturing", "large", "CNY", "Chinese electronics connector and cable manufacturer"),
    
    # Electric Vehicles & New Energy
    "002594.SZ": Stock("002594.SZ", "BYD Company Limited", "SZSE", "China", "Consumer Discretionary", "Electric Vehicles", "large", "CNY", "Leading Chinese electric vehicle and battery manufacturer"),
    "002129.SZ": Stock("002129.SZ", "TCL Technology Group Corporation", "SZSE", "China", "Technology", "Display Technology", "large", "CNY", "Chinese display panel and consumer electronics manufacturer"),
    
    # === CHINEXT GROWTH ENTERPRISE MARKET ===
    # Battery & Energy Technology
    "300750.SZ": Stock("300750.SZ", "Contemporary Amperex Technology Co., Limited", "CHINEXT", "China", "Technology", "Battery Technology", "large", "CNH", "World's largest battery manufacturer for electric vehicles"),
    "300014.SZ": Stock("300014.SZ", "Eve Energy Co., Ltd.", "CHINEXT", "China", "Technology", "Battery Technology", "large", "CNH", "Chinese lithium battery manufacturer"),
    "300274.SZ": Stock("300274.SZ", "Sungrow Power Supply Co., Ltd.", "CHINEXT", "China", "Technology", "Solar Energy", "large", "CNH", "Leading Chinese solar inverter manufacturer"),
    
    # Financial Technology & Services
    "300059.SZ": Stock("300059.SZ", "East Money Information Co., Ltd.", "CHINEXT", "China", "Technology", "Financial Technology", "large", "CNH", "Leading Chinese financial information and services provider"),
    "300142.SZ": Stock("300142.SZ", "Walvax Biotechnology Co., Ltd.", "CHINEXT", "China", "Healthcare", "Biotechnology", "mid", "CNH", "Chinese vaccine and biotechnology company"),
    
    # Healthcare & Medical Services
    "300015.SZ": Stock("300015.SZ", "Aier Eye Hospital Group Co., Ltd.", "CHINEXT", "China", "Healthcare", "Medical Services", "large", "CNH", "Largest private eye hospital chain in China"),
    "300760.SZ": Stock("300760.SZ", "Mindray Medical International Limited", "CHINEXT", "China", "Healthcare", "Medical Devices", "large", "CNH", "Leading Chinese medical equipment manufacturer"),
    "300003.SZ": Stock("300003.SZ", "Lepu Medical Technology Co., Ltd.", "CHINEXT", "China", "Healthcare", "Medical Devices", "mid", "CNH", "Chinese medical device and pharmaceutical company"),
    
    # Internet & Technology Services
    "300408.SZ": Stock("300408.SZ", "Chaozhou Three-Circle Group Co., Ltd.", "CHINEXT", "China", "Technology", "Electronic Components", "mid", "CNH", "Chinese electronic components manufacturer"),
    "300001.SZ": Stock("300001.SZ", "Qingdao Tgood Electric Co., Ltd.", "CHINEXT", "China", "Technology", "Electric Equipment", "mid", "CNH", "Chinese electrical equipment manufacturer"),
    
    # Telecommunications & Electronics
    "300035.SZ": Stock("300035.SZ", "Hunan Zhongke Electric Co., Ltd.", "CHINEXT", "China", "Technology", "Electric Equipment", "mid", "CNH", "Chinese power equipment manufacturer"),
    "300215.SZ": Stock("300215.SZ", "Suzhou Electrical Apparatus Science Academy Co., Ltd.", "CHINEXT", "China", "Technology", "Electric Equipment", "mid", "CNH", "Chinese electrical equipment and automation company"),
    
    # Automotive & Transportation
    "300124.SZ": Stock("300124.SZ", "Shenzhen Inovance Technology Co., Ltd.", "CHINEXT", "China", "Technology", "Industrial Automation", "large", "CNH", "Chinese industrial automation and new energy vehicle components"),
    "300033.SZ": Stock("300033.SZ", "Tongyu Heavy Industry Co., Ltd.", "CHINEXT", "China", "Industrials", "Heavy Machinery", "mid", "CNH", "Chinese heavy machinery manufacturer"),
    
    # New Materials & Chemicals
    "300037.SZ": Stock("300037.SZ", "Xinyu Iron & Steel Co., Ltd.", "CHINEXT", "China", "Materials", "Steel", "mid", "CNH", "Chinese steel and materials company"),
    "300068.SZ": Stock("300068.SZ", "Nanjing Sample Technology Co., Ltd.", "CHINEXT", "China", "Technology", "Software", "mid", "CNH", "Chinese software and technology services company"),
    
    # Solar & Renewable Energy
    "300093.SZ": Stock("300093.SZ", "Gansu Golden Solar Co., Ltd.", "CHINEXT", "China", "Technology", "Solar Energy", "mid", "CNH", "Chinese solar energy equipment manufacturer"),
    "301658.SZ": Stock("301658.SZ", "Shenzhen Sofarsolar Co., Ltd.", "CHINEXT", "China", "Technology", "Solar Energy", "mid", "CNH", "Chinese solar inverter and energy storage systems manufacturer"),
    
    # Pharmaceuticals & Biotechnology
    "300009.SZ": Stock("300009.SZ", "Anhui Anke Biotechnology Group Co., Ltd.", "CHINEXT", "China", "Healthcare", "Biotechnology", "mid", "CNH", "Chinese biotechnology and pharmaceutical company"),
    "300109.SZ": Stock("300109.SZ", "NKY Medical Holdings Ltd.", "CHINEXT", "China", "Healthcare", "Medical Services", "mid", "CNH", "Chinese medical services company"),
    
    # Advanced Manufacturing
    "300516.SZ": Stock("300516.SZ", "Shenzhen Vapel Power Supply Co., Ltd.", "CHINEXT", "China", "Technology", "Power Electronics", "mid", "CNH", "Chinese power supply and electronics manufacturer"),
    "300020.SZ": Stock("300020.SZ", "Enjoyor Technology Co., Ltd.", "CHINEXT", "China", "Technology", "Software", "mid", "CNH", "Chinese software and information technology company"),
}
