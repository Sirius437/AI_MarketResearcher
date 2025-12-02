"""
Shanghai Stock Exchange (SSE) stocks - Comprehensive listing of major Chinese companies.
Includes both main board (600xxx, 601xxx) and STAR Market (688xxx) stocks.
"""

from ..models import Stock

# Shanghai Stock Exchange stocks - Expanded comprehensive listing
SSE_STOCKS = {
    # === TECHNOLOGY & SEMICONDUCTORS ===
    "600036.SS": Stock("600036.SS", "China Merchants Bank Co., Ltd.", "SSE", "China", "Financials", "Banking", "large", "CNY", "Leading Chinese commercial bank with strong digital banking"),
    "600519.SS": Stock("600519.SS", "Kweichow Moutai Co., Ltd.", "SSE", "China", "Consumer Staples", "Beverages", "large", "CNY", "Premium Chinese liquor brand, most valuable Chinese company"),
    "600745.SS": Stock("600745.SS", "CRRC Corporation Limited", "SSE", "China", "Industrials", "Rail Equipment", "large", "CNY", "World's largest rolling stock manufacturer"),
    "600887.SS": Stock("600887.SS", "Inner Mongolia Yili Industrial Group Co., Ltd.", "SSE", "China", "Consumer Staples", "Food Products", "large", "CNY", "Leading Chinese dairy products company"),
    "601012.SS": Stock("601012.SS", "Longi Green Energy Technology Co., Ltd.", "SSE", "China", "Technology", "Solar Energy", "large", "CNY", "Leading solar technology and equipment manufacturer"),
    "601318.SS": Stock("601318.SS", "Ping An Insurance Group Company of China, Ltd.", "SSE", "China", "Financials", "Insurance", "large", "CNY", "Major Chinese insurance and financial services group"),
    "601398.SS": Stock("601398.SS", "Industrial and Commercial Bank of China Limited", "SSE", "China", "Financials", "Banking", "large", "CNY", "World's largest bank by total assets"),
    "601728.SS": Stock("601728.SS", "China Telecom Corporation Limited", "SSE", "China", "Communication Services", "Telecommunications", "large", "CNY", "Major Chinese telecommunications operator"),
    "601857.SS": Stock("601857.SS", "PetroChina Company Limited", "SSE", "China", "Energy", "Oil & Gas", "large", "CNY", "China's largest oil and gas producer"),
    "601888.SS": Stock("601888.SS", "China Tourism Group Duty Free Corporation Limited", "SSE", "China", "Consumer Discretionary", "Retail", "large", "CNY", "Leading duty-free retail operator"),
    
    # === STAR MARKET (SCIENCE & TECHNOLOGY INNOVATION BOARD) ===
    "688001.SS": Stock("688001.SS", "Suzhou HYC Technology Co., Ltd.", "SEHKSTAR", "China", "Technology", "Semiconductors", "mid", "CNH", "Semiconductor equipment and technology solutions"),
    "688002.SS": Stock("688002.SS", "Raytron Technology Co., Ltd.", "SEHKSTAR", "China", "Technology", "Semiconductors", "mid", "CNH", "Infrared thermal imaging and sensor technology"),
    "688008.SS": Stock("688008.SS", "Montage Technology Co., Ltd.", "SEHKSTAR", "China", "Technology", "Semiconductors", "mid", "CNH", "Memory interface and connectivity chip solutions"),
    "688009.SS": Stock("688009.SS", "China Railway Signal & Communication Corporation Limited", "SEHKSTAR", "China", "Industrials", "Transportation Technology", "large", "CNH", "Railway signaling and communication systems"),
    "688012.SS": Stock("688012.SS", "Advanced Micro-Fabrication Equipment Inc.", "SEHKSTAR", "China", "Technology", "Semiconductor Equipment", "mid", "CNH", "Semiconductor manufacturing equipment"),
    "688016.SS": Stock("688016.SS", "Shanghai Microport Endovascular MedTech Co., Ltd.", "SEHKSTAR", "China", "Healthcare", "Medical Devices", "mid", "CNH", "Endovascular medical devices and solutions"),
    "688018.SS": Stock("688018.SS", "Espressif Systems Shanghai Co., Ltd.", "SEHKSTAR", "China", "Technology", "Semiconductors", "mid", "CNH", "Wi-Fi and Bluetooth connectivity chips"),
    "688025.SS": Stock("688025.SS", "Shenzhen JPT Opto-electronics Co., Ltd.", "SEHKSTAR", "China", "Technology", "Laser Technology", "mid", "CNH", "Industrial laser equipment and solutions"),
    "688036.SS": Stock("688036.SS", "Shenzhen Transsion Holdings Co., Ltd.", "SEHKSTAR", "China", "Technology", "Consumer Electronics", "large", "CNH", "Mobile phone manufacturer focused on African markets"),
    "688041.SS": Stock("688041.SS", "Hygon Information Technology Co., Ltd.", "SEHKSTAR", "China", "Technology", "Processors", "mid", "CNH", "High-performance processors and server solutions"),
    "688047.SS": Stock("688047.SS", "Loongson Technology Corporation Limited", "SEHKSTAR", "China", "Technology", "Processors", "mid", "CNH", "Domestic CPU and processor technology"),
    "688072.SS": Stock("688072.SS", "Piotech Inc.", "SEHKSTAR", "China", "Technology", "Semiconductor Equipment", "mid", "CNH", "Plasma processing equipment for semiconductors"),
    
    # === BANKING & FINANCIAL SERVICES ===
    "600000.SS": Stock("600000.SS", "Pudong Development Bank Co., Ltd.", "SSE", "China", "Financials", "Banking", "large", "CNY", "Major Chinese joint-stock commercial bank"),
    "600015.SS": Stock("600015.SS", "Hua Xia Bank Co., Limited", "SSE", "China", "Financials", "Banking", "large", "CNY", "National joint-stock commercial bank"),
    "600016.SS": Stock("600016.SS", "China Minsheng Banking Corp., Ltd.", "SSE", "China", "Financials", "Banking", "large", "CNY", "First privately-owned bank in mainland China"),
    "601166.SS": Stock("601166.SS", "Industrial Bank Co., Ltd.", "SSE", "China", "Financials", "Banking", "large", "CNY", "Leading Chinese commercial bank"),
    "601288.SS": Stock("601288.SS", "Agricultural Bank of China Limited", "SSE", "China", "Financials", "Banking", "large", "CNY", "One of China's Big Four state-owned banks"),
    "601328.SS": Stock("601328.SS", "Bank of Communications Co., Ltd.", "SSE", "China", "Financials", "Banking", "large", "CNY", "One of China's oldest and largest banks"),
    "601601.SS": Stock("601601.SS", "China Pacific Insurance Group Co., Ltd.", "SSE", "China", "Financials", "Insurance", "large", "CNY", "Major Chinese insurance company"),
    "601628.SS": Stock("601628.SS", "China Life Insurance Company Limited", "SSE", "China", "Financials", "Insurance", "large", "CNY", "China's largest life insurance company"),
    "601988.SS": Stock("601988.SS", "Bank of China Limited", "SSE", "China", "Financials", "Banking", "large", "CNY", "One of China's Big Four state-owned banks"),
    
    # === ENERGY & UTILITIES ===
    "600028.SS": Stock("600028.SS", "China Petroleum & Chemical Corporation", "SSE", "China", "Energy", "Oil & Gas", "large", "CNY", "Major Chinese petroleum and petrochemical company"),
    "600900.SS": Stock("600900.SS", "China Yangtze Power Co., Ltd.", "SSE", "China", "Utilities", "Electric Power", "large", "CNY", "China's largest hydroelectric power company"),
    "601088.SS": Stock("601088.SS", "China Shenhua Energy Company Limited", "SSE", "China", "Energy", "Coal", "large", "CNY", "China's largest coal mining company"),
    "601225.SS": Stock("601225.SS", "Shaanxi Coal Industry Company Limited", "SSE", "China", "Energy", "Coal", "large", "CNY", "Major Chinese coal mining and chemical company"),
    "601898.SS": Stock("601898.SS", "China Coal Energy Company Limited", "SSE", "China", "Energy", "Coal", "large", "CNY", "Integrated coal mining and energy company"),
    
    # === MATERIALS & MINING ===
    "600019.SS": Stock("600019.SS", "Baoshan Iron & Steel Co., Ltd.", "SSE", "China", "Materials", "Steel", "large", "CNY", "China's largest steel producer"),
    "600585.SS": Stock("600585.SS", "Anhui Conch Cement Company Limited", "SSE", "China", "Materials", "Construction Materials", "large", "CNY", "Leading Chinese cement manufacturer"),
    "601899.SS": Stock("601899.SS", "Zijin Mining Group Co., Ltd.", "SSE", "China", "Materials", "Mining", "large", "CNY", "Major Chinese gold and copper mining company"),
    "601600.SS": Stock("601600.SS", "Aluminum Corporation of China Limited", "SSE", "China", "Materials", "Aluminum", "large", "CNY", "China's largest aluminum producer"),
    
    # === CONSUMER GOODS & RETAIL ===
    "600309.SS": Stock("600309.SS", "Wanhua Chemical Group Co., Ltd.", "SSE", "China", "Materials", "Chemicals", "large", "CNY", "Leading polyurethane and petrochemical company"),
    "600690.SS": Stock("600690.SS", "Qingdao Haier Biomedical Co., Ltd.", "SSE", "China", "Healthcare", "Medical Equipment", "mid", "CNY", "Biomedical cold chain equipment manufacturer"),
    "600809.SS": Stock("600809.SS", "Shanxi Xinghuacun Fen Wine Factory Co., Ltd.", "SSE", "China", "Consumer Staples", "Beverages", "large", "CNY", "Premium Chinese liquor producer"),
    "600872.SS": Stock("600872.SS", "Center Laboratories, Inc.", "SSE", "China", "Healthcare", "Pharmaceuticals", "mid", "CNY", "Pharmaceutical and healthcare products"),
    "601888.SS": Stock("601888.SS", "China Tourism Group Duty Free Corporation Limited", "SSE", "China", "Consumer Discretionary", "Retail", "large", "CNY", "Leading duty-free retail operator in China"),
    
    # === HEALTHCARE & PHARMACEUTICALS ===
    "600276.SS": Stock("600276.SS", "Jiangsu Hengrui Medicine Co., Ltd.", "SSE", "China", "Healthcare", "Pharmaceuticals", "large", "CNY", "Leading Chinese pharmaceutical company"),
    "600196.SS": Stock("600196.SS", "Fosun Pharma Co., Ltd.", "SSE", "China", "Healthcare", "Pharmaceuticals", "large", "CNY", "Integrated healthcare and pharmaceutical group"),
    "600867.SS": Stock("600867.SS", "Tonghua Dongbao Pharmaceutical Co., Ltd.", "SSE", "China", "Healthcare", "Pharmaceuticals", "mid", "CNY", "Diabetes care and pharmaceutical products"),
    
    # === REAL ESTATE & CONSTRUCTION ===
    "600048.SS": Stock("600048.SS", "Poly Developments and Holdings Group Co., Ltd.", "SSE", "China", "Real Estate", "Real Estate Development", "large", "CNY", "Major Chinese real estate developer"),
    "600340.SS": Stock("600340.SS", "China Fortune Land Development Co., Ltd.", "SSE", "China", "Real Estate", "Real Estate Development", "large", "CNY", "Industrial park development and operation"),
    "601155.SS": Stock("601155.SS", "Xinhua Winshare Publishing and Media Co., Ltd.", "SSE", "China", "Communication Services", "Publishing", "mid", "CNY", "Publishing and media services"),
    
    # === INDUSTRIALS & TRANSPORTATION ===
    "600009.SS": Stock("600009.SS", "Shanghai International Airport Co., Ltd.", "SSE", "China", "Industrials", "Transportation", "large", "CNY", "Shanghai Pudong International Airport operator"),
    "600115.SS": Stock("600115.SS", "Orient Securities Company Limited", "SSE", "China", "Financials", "Securities", "large", "CNY", "Securities brokerage and investment services"),
    "600170.SS": Stock("600170.SS", "Shanghai Construction Group Co., Ltd.", "SSE", "China", "Industrials", "Construction", "large", "CNY", "Major Chinese construction and engineering company"),
    "601766.SS": Stock("601766.SS", "CRRC Corporation Limited", "SSE", "China", "Industrials", "Transportation Equipment", "large", "CNY", "World's largest rolling stock manufacturer"),
    "601919.SS": Stock("601919.SS", "COSCO SHIPPING Holdings Co., Ltd.", "SSE", "China", "Industrials", "Marine Transportation", "large", "CNY", "Major Chinese shipping and logistics company"),
    
    # === TELECOMMUNICATIONS ===
    "600050.SS": Stock("600050.SS", "China United Network Communications Limited", "SSE", "China", "Communication Services", "Telecommunications", "large", "CNY", "Major Chinese telecommunications operator"),
}
