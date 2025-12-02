"""
Korea Exchange (KRX) stocks - Comprehensive listing of major Korean companies.
Includes companies from KSE integration and major Korean corporations across all sectors.
"""

from ..models import Stock

# Korea Exchange stocks
KRX_STOCKS = {
    # === TECHNOLOGY & SEMICONDUCTORS ===
    "005930.KS": Stock("005930.KS", "Samsung Electronics Co., Ltd.", "KSE", "South Korea", "Technology", "Consumer Electronics", "large", "KRW", "World's largest memory chip and smartphone manufacturer"),
    "000660.KS": Stock("000660.KS", "SK Hynix Inc.", "KSE", "South Korea", "Technology", "Semiconductors", "large", "KRW", "World's second-largest memory semiconductor supplier"),
    "006400.KS": Stock("006400.KS", "Samsung SDI Co., Ltd.", "KSE", "South Korea", "Technology", "Battery Technology", "large", "KRW", "Leading battery manufacturer for EVs and energy storage"),
    "042700.KS": Stock("042700.KS", "Hanmi Semiconductor Inc.", "KSE", "South Korea", "Technology", "Semiconductor Equipment", "mid", "KRW", "Semiconductor assembly and test equipment manufacturer"),
    
    # === INTERNET & DIGITAL SERVICES ===
    "035420.KS": Stock("035420.KS", "NAVER Corporation", "KSE", "South Korea", "Technology", "Internet Services", "large", "KRW", "South Korea's largest search engine and online platform operator"),
    "035720.KS": Stock("035720.KS", "Kakao Corp.", "KSE", "South Korea", "Technology", "Internet Services", "large", "KRW", "Leading mobile platform company operating KakaoTalk messenger"),
    "376300.KS": Stock("376300.KS", "Digieco Co., Ltd.", "KSE", "South Korea", "Technology", "Software", "small", "KRW", "Software development and IT services company"),
    "067160.KS": Stock("067160.KS", "Afreeca TV Co., Ltd.", "KSE", "South Korea", "Communication Services", "Digital Media", "mid", "KRW", "Live streaming and digital content platform"),
    
    # === AUTOMOTIVE ===
    "005380.KS": Stock("005380.KS", "Hyundai Motor Company", "KSE", "South Korea", "Consumer Discretionary", "Automotive", "large", "KRW", "South Korea's largest automotive manufacturer"),
    "000270.KS": Stock("000270.KS", "Kia Corporation", "KSE", "South Korea", "Consumer Discretionary", "Automotive", "large", "KRW", "Major automotive manufacturer, subsidiary of Hyundai Motor Group"),
    "012330.KS": Stock("012330.KS", "Hyundai Mobis Co., Ltd.", "KSE", "South Korea", "Consumer Discretionary", "Auto Parts", "large", "KRW", "Leading automotive parts supplier"),
    "161390.KS": Stock("161390.KS", "Hanwha Q Cells Co., Ltd.", "KSE", "South Korea", "Energy", "Solar Energy", "large", "KRW", "Global solar cell and module manufacturer"),
    
    # === CHEMICALS & MATERIALS ===
    "051910.KS": Stock("051910.KS", "LG Chem Ltd.", "KSE", "South Korea", "Materials", "Chemicals", "large", "KRW", "Leading chemical company and battery manufacturer"),
    "005490.KS": Stock("005490.KS", "POSCO Holdings Inc.", "KSE", "South Korea", "Materials", "Steel", "large", "KRW", "South Korea's largest steel-making company"),
    "010950.KS": Stock("010950.KS", "S-Oil Corporation", "KSE", "South Korea", "Energy", "Oil Refining", "large", "KRW", "Major oil refining company"),
    "011170.KS": Stock("011170.KS", "Lotte Chemical Corporation", "KSE", "South Korea", "Materials", "Chemicals", "large", "KRW", "Petrochemical and chemical company"),
    
    # === FINANCIAL SERVICES ===
    "055550.KS": Stock("055550.KS", "Shinhan Financial Group Co., Ltd.", "KSE", "South Korea", "Financials", "Banking", "large", "KRW", "Major banking and financial services company"),
    "086790.KS": Stock("086790.KS", "Hana Financial Group Inc.", "KSE", "South Korea", "Financials", "Banking", "large", "KRW", "Leading financial services company"),
    "105560.KS": Stock("105560.KS", "KB Financial Group Inc.", "KSE", "South Korea", "Financials", "Banking", "large", "KRW", "Largest banking and financial services company"),
    "316140.KS": Stock("316140.KS", "Woori Financial Group Inc.", "KSE", "South Korea", "Financials", "Banking", "large", "KRW", "Major banking group"),
    
    # === HEALTHCARE & BIOTECHNOLOGY ===
    "207940.KS": Stock("207940.KS", "Samsung Biologics Co., Ltd.", "KSE", "South Korea", "Healthcare", "Biotechnology", "large", "KRW", "Leading contract development and manufacturing organization"),
    "068270.KS": Stock("068270.KS", "Celltrion Inc.", "KSE", "South Korea", "Healthcare", "Biotechnology", "large", "KRW", "Biopharmaceutical company specializing in biosimilars"),
    "326030.KS": Stock("326030.KS", "SK Biopharmaceuticals Co., Ltd.", "KSE", "South Korea", "Healthcare", "Pharmaceuticals", "large", "KRW", "Pharmaceutical company focusing on CNS disorders"),
    "302440.KS": Stock("302440.KS", "SK Bioscience Co., Ltd.", "KSE", "South Korea", "Healthcare", "Biotechnology", "large", "KRW", "Vaccine and biotechnology company"),
    
    # === INDUSTRIALS & CONSTRUCTION ===
    "028260.KS": Stock("028260.KS", "Samsung C&T Corporation", "KSE", "South Korea", "Industrials", "Construction", "large", "KRW", "Major construction and trading company"),
    "009540.KS": Stock("009540.KS", "HD Korea Shipbuilding & Offshore Engineering Co., Ltd.", "KSE", "South Korea", "Industrials", "Shipbuilding", "large", "KRW", "Leading shipbuilding company"),
    "010140.KS": Stock("010140.KS", "Samsung Heavy Industries Co., Ltd.", "KSE", "South Korea", "Industrials", "Shipbuilding", "large", "KRW", "Major shipbuilding and offshore platform company"),
    "000720.KS": Stock("000720.KS", "Hyundai Engineering & Construction Co., Ltd.", "KSE", "South Korea", "Industrials", "Construction", "large", "KRW", "Leading construction company"),
    
    # === CONSUMER GOODS & RETAIL ===
    "000120.KS": Stock("000120.KS", "CJ CheilJedang Corp.", "KSE", "South Korea", "Consumer Staples", "Food Products", "large", "KRW", "Food and biotechnology company"),
    "097950.KS": Stock("097950.KS", "CJ CheilJedang BIO", "KSE", "South Korea", "Materials", "Biotechnology", "large", "KRW", "Bio-based materials and food ingredients company"),
    "282330.KS": Stock("282330.KS", "BGF Retail Co., Ltd.", "KSE", "South Korea", "Consumer Discretionary", "Retail", "mid", "KRW", "Convenience store operator (CU stores)"),
    "051600.KS": Stock("051600.KS", "Korean Air Lines Co., Ltd.", "KSE", "South Korea", "Industrials", "Airlines", "large", "KRW", "Flag carrier airline of South Korea"),
    
    # === ENTERTAINMENT & MEDIA ===
    "041510.KS": Stock("041510.KS", "SM Entertainment Co., Ltd.", "KSE", "South Korea", "Communication Services", "Entertainment", "mid", "KRW", "Leading K-pop entertainment company"),
    "122870.KS": Stock("122870.KS", "YG Entertainment Inc.", "KSE", "South Korea", "Communication Services", "Entertainment", "mid", "KRW", "Major K-pop entertainment company"),
    "352820.KS": Stock("352820.KS", "Hybe Co., Ltd.", "KSE", "South Korea", "Communication Services", "Entertainment", "large", "KRW", "Entertainment company behind BTS and other K-pop acts"),
    "034220.KS": Stock("034220.KS", "LG Display Co., Ltd.", "KSE", "South Korea", "Technology", "Display Technology", "large", "KRW", "Leading display panel manufacturer"),
    
    # === ENERGY & UTILITIES ===
    "015760.KS": Stock("015760.KS", "Korea Electric Power Corporation", "KSE", "South Korea", "Utilities", "Electric Utilities", "large", "KRW", "South Korea's largest electric utility company"),
    "267250.KS": Stock("267250.KS", "HD Hyundai Heavy Industries Co., Ltd.", "KSE", "South Korea", "Industrials", "Heavy Machinery", "large", "KRW", "Heavy industries and shipbuilding company"),
    "003490.KS": Stock("003490.KS", "Korean Air Lines Co., Ltd.", "KSE", "South Korea", "Industrials", "Airlines", "large", "KRW", "National flag carrier airline"),
    
    # === TELECOMMUNICATIONS ===
    "030200.KS": Stock("030200.KS", "KT Corporation", "KSE", "South Korea", "Communication Services", "Telecommunications", "large", "KRW", "Major telecommunications company"),
    "017670.KS": Stock("017670.KS", "SK Telecom Co., Ltd.", "KSE", "South Korea", "Communication Services", "Telecommunications", "large", "KRW", "South Korea's largest mobile operator"),
    "032640.KS": Stock("032640.KS", "LG Uplus Corp.", "KSE", "South Korea", "Communication Services", "Telecommunications", "large", "KRW", "Third-largest mobile carrier in South Korea"),
    
    # === SPECIALTY SECTORS ===
    "003670.KS": Stock("003670.KS", "Posco International Corporation", "KSE", "South Korea", "Industrials", "Trading Company", "large", "KRW", "Trading and investment company"),
    "018260.KS": Stock("018260.KS", "Samsung SDS Co., Ltd.", "KSE", "South Korea", "Technology", "IT Services", "large", "KRW", "IT services and solutions company"),
    "000810.KS": Stock("000810.KS", "Samsung Fire & Marine Insurance Co., Ltd.", "KSE", "South Korea", "Financials", "Insurance", "large", "KRW", "Leading insurance company"),
}
