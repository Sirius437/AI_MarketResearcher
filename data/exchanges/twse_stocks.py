"""
Taiwan Stock Exchange (TWSE) listed stocks - Comprehensive listing of major Taiwanese companies.
Includes companies from TWSE integration and major Taiwanese corporations across all sectors.
"""

from ..models import Stock

TWSE_STOCKS = {
    # === TECHNOLOGY & SEMICONDUCTORS ===
    "2330": Stock("2330", "Taiwan Semiconductor Manufacturing Co., Ltd.", "TWSE", "Taiwan", "Technology", "Semiconductors", "large", "TWD", "World's largest contract chip manufacturer and foundry services"),
    "2454": Stock("2454", "MediaTek Inc.", "TWSE", "Taiwan", "Technology", "Semiconductors", "large", "TWD", "Leading fabless semiconductor company specializing in wireless communications and digital multimedia solutions"),
    "3034": Stock("3034", "Novatek Microelectronics Corp.", "TWSE", "Taiwan", "Technology", "Semiconductors", "large", "TWD", "Leading display driver IC and SoC design company"),
    "2408": Stock("2408", "Nanya Technology Corp.", "TWSE", "Taiwan", "Technology", "Memory", "large", "TWD", "Major DRAM memory manufacturer"),
    "3711": Stock("3711", "ASE Technology Holding Co., Ltd.", "TWSE", "Taiwan", "Technology", "Semiconductor Services", "large", "TWD", "World's largest semiconductor assembly and test services provider"),
    "6770": Stock("6770", "Powerchip Semiconductor Manufacturing Corp.", "TWSE", "Taiwan", "Technology", "Semiconductors", "large", "TWD", "Memory and logic semiconductor foundry services"),
    "2379": Stock("2379", "Realtek Semiconductor Corp.", "TWSE", "Taiwan", "Technology", "Semiconductors", "large", "TWD", "Leading IC design company for communications network and multimedia applications"),
    "3037": Stock("3037", "Unimicron Technology Corp.", "TWSE", "Taiwan", "Technology", "PCB", "large", "TWD", "Leading printed circuit board manufacturer"),
    "2344": Stock("2344", "Winbond Electronics Corp.", "TWSE", "Taiwan", "Technology", "Memory", "large", "TWD", "Specialty memory IC manufacturer"),
    "4919": Stock("4919", "Nuvoton Technology Corp.", "TWSE", "Taiwan", "Technology", "Semiconductors", "large", "TWD", "Microcontroller and mixed-signal IC design company"),

    # === ELECTRONICS & HARDWARE ===
    "2317": Stock("2317", "Hon Hai Precision Industry Co., Ltd.", "TWSE", "Taiwan", "Technology", "Electronics Manufacturing", "large", "TWD", "World's largest electronics contract manufacturer (Foxconn)"),
    "2382": Stock("2382", "Quanta Computer Inc.", "TWSE", "Taiwan", "Technology", "Computer Hardware", "large", "TWD", "Leading notebook computer and server manufacturer"),
    "2357": Stock("2357", "ASUSTeK Computer Inc.", "TWSE", "Taiwan", "Technology", "Computer Hardware", "large", "TWD", "Leading computer hardware and electronics company"),
    "2353": Stock("2353", "Acer Inc.", "TWSE", "Taiwan", "Technology", "Computer Hardware", "large", "TWD", "Global PC and technology company"),
    "3231": Stock("3231", "Wistron Corp.", "TWSE", "Taiwan", "Technology", "Electronics Manufacturing", "large", "TWD", "Major electronics contract manufacturer"),
    "4938": Stock("4938", "Pegatron Corp.", "TWSE", "Taiwan", "Technology", "Electronics Manufacturing", "large", "TWD", "Electronics manufacturing services company"),
    "2324": Stock("2324", "Compal Electronics, Inc.", "TWSE", "Taiwan", "Technology", "Electronics Manufacturing", "large", "TWD", "Leading notebook computer manufacturer"),
    "2356": Stock("2356", "Inventec Corp.", "TWSE", "Taiwan", "Technology", "Electronics Manufacturing", "large", "TWD", "Electronics contract manufacturer"),
    "2376": Stock("2376", "Gigabyte Technology Co., Ltd.", "TWSE", "Taiwan", "Technology", "Computer Hardware", "large", "TWD", "Motherboard and graphics card manufacturer"),
    "2377": Stock("2377", "Micro-Star International Co., Ltd.", "TWSE", "Taiwan", "Technology", "Computer Hardware", "large", "TWD", "Computer hardware manufacturer (MSI)"),

    # === DISPLAY & OPTOELECTRONICS ===
    "2409": Stock("2409", "AU Optronics Corp.", "TWSE", "Taiwan", "Technology", "Display Technology", "large", "TWD", "Leading TFT-LCD panel manufacturer"),
    "3481": Stock("3481", "Innolux Corp.", "TWSE", "Taiwan", "Technology", "Display Technology", "large", "TWD", "Major TFT-LCD panel manufacturer"),
    "3008": Stock("3008", "Largan Precision Co., Ltd.", "TWSE", "Taiwan", "Technology", "Optical Components", "large", "TWD", "Leading smartphone camera lens manufacturer"),
    "3019": Stock("3019", "Asia Optical Co., Inc.", "TWSE", "Taiwan", "Technology", "Optical Components", "large", "TWD", "Optical components and digital camera manufacturer"),
    "2393": Stock("2393", "Everlight Electronics Co., Ltd.", "TWSE", "Taiwan", "Technology", "LED", "large", "TWD", "Leading LED and optoelectronics manufacturer"),
    "3714": Stock("3714", "Ennostar Inc.", "TWSE", "Taiwan", "Technology", "LED", "large", "TWD", "LED epitaxial wafer and chip manufacturer"),

    # === POWER & ELECTRONICS COMPONENTS ===
    "2308": Stock("2308", "Delta Electronics, Inc.", "TWSE", "Taiwan", "Technology", "Power Electronics", "large", "TWD", "Leading power electronics and energy management solutions provider"),
    "2327": Stock("2327", "Yageo Corp.", "TWSE", "Taiwan", "Technology", "Electronic Components", "large", "TWD", "Leading passive component manufacturer"),
    "2301": Stock("2301", "Lite-On Technology Corp.", "TWSE", "Taiwan", "Technology", "Electronic Components", "large", "TWD", "Optoelectronics and electronic components manufacturer"),
    "2474": Stock("2474", "Catcher Technology Co., Ltd.", "TWSE", "Taiwan", "Technology", "Metal Casings", "large", "TWD", "Leading metal casing manufacturer for consumer electronics"),
    "6415": Stock("6415", "Silergy Corp.", "TWSE", "Taiwan", "Technology", "Power Management", "large", "TWD", "Analog and mixed-signal IC design company"),

    # === TELECOMMUNICATIONS ===
    "2412": Stock("2412", "Chunghwa Telecom Co., Ltd.", "TWSE", "Taiwan", "Communication Services", "Telecommunications", "large", "TWD", "Taiwan's largest telecommunications company"),
    "3045": Stock("3045", "Taiwan Mobile Co., Ltd.", "TWSE", "Taiwan", "Communication Services", "Telecommunications", "large", "TWD", "Major mobile telecommunications operator"),
    "4904": Stock("4904", "Far EasTone Telecommunications Co., Ltd.", "TWSE", "Taiwan", "Communication Services", "Telecommunications", "large", "TWD", "Leading mobile telecommunications operator"),

    # === FINANCIAL SERVICES ===
    "2881": Stock("2881", "Fubon Financial Holding Co., Ltd.", "TWSE", "Taiwan", "Financials", "Banking", "large", "TWD", "Leading financial services holding company"),
    "2882": Stock("2882", "Cathay Financial Holding Co., Ltd.", "TWSE", "Taiwan", "Financials", "Banking", "large", "TWD", "Major financial services holding company"),
    "2880": Stock("2880", "Hua Nan Financial Holdings Co., Ltd.", "TWSE", "Taiwan", "Financials", "Banking", "large", "TWD", "Financial services holding company"),
    "2886": Stock("2886", "Mega Financial Holding Co., Ltd.", "TWSE", "Taiwan", "Financials", "Banking", "large", "TWD", "Major banking and financial services group"),
    "2884": Stock("2884", "E.Sun Financial Holding Co., Ltd.", "TWSE", "Taiwan", "Financials", "Banking", "large", "TWD", "Financial services holding company"),
    "2891": Stock("2891", "CTBC Financial Holding Co., Ltd.", "TWSE", "Taiwan", "Financials", "Banking", "large", "TWD", "Leading financial services group"),
    "2892": Stock("2892", "First Financial Holding Co., Ltd.", "TWSE", "Taiwan", "Financials", "Banking", "large", "TWD", "Financial services holding company"),
    "2885": Stock("2885", "Yuanta Financial Holding Co., Ltd.", "TWSE", "Taiwan", "Financials", "Banking", "large", "TWD", "Financial services and securities company"),

    # === PETROCHEMICALS & MATERIALS ===
    "1301": Stock("1301", "Formosa Plastics Corp.", "TWSE", "Taiwan", "Materials", "Chemicals", "large", "TWD", "Leading petrochemical company"),
    "1303": Stock("1303", "Nan Ya Plastics Corp.", "TWSE", "Taiwan", "Materials", "Plastics", "large", "TWD", "Major plastics and chemical manufacturer"),
    "1326": Stock("1326", "Formosa Chemicals & Fibre Corp.", "TWSE", "Taiwan", "Materials", "Chemicals", "large", "TWD", "Integrated petrochemical company"),
    "6505": Stock("6505", "Formosa Petrochemical Corp.", "TWSE", "Taiwan", "Energy", "Oil Refining", "large", "TWD", "Major oil refining and petrochemical company"),
    "1402": Stock("1402", "Far Eastern New Century Corp.", "TWSE", "Taiwan", "Materials", "Textiles", "large", "TWD", "Polyester and textile manufacturer"),

    # === STEEL & METALS ===
    "2002": Stock("2002", "China Steel Corp.", "TWSE", "Taiwan", "Materials", "Steel", "large", "TWD", "Taiwan's largest steel company"),
    "2006": Stock("2006", "Tung Ho Steel Enterprise Corp.", "TWSE", "Taiwan", "Materials", "Steel", "large", "TWD", "Steel manufacturing company"),
    "2049": Stock("2049", "Hiwin Technologies Corp.", "TWSE", "Taiwan", "Industrials", "Industrial Automation", "large", "TWD", "Linear motion and automation technology manufacturer"),

    # === TRANSPORTATION & LOGISTICS ===
    "2603": Stock("2603", "Evergreen Marine Corp., Ltd.", "TWSE", "Taiwan", "Industrials", "Shipping", "large", "TWD", "Major container shipping company"),
    "2609": Stock("2609", "Yang Ming Marine Transport Corp.", "TWSE", "Taiwan", "Industrials", "Shipping", "large", "TWD", "Container shipping and logistics company"),
    "2615": Stock("2615", "Wan Hai Lines Ltd.", "TWSE", "Taiwan", "Industrials", "Shipping", "large", "TWD", "Container shipping company"),
    "2610": Stock("2610", "China Airlines Ltd.", "TWSE", "Taiwan", "Industrials", "Airlines", "large", "TWD", "Taiwan's flag carrier airline"),
    "2618": Stock("2618", "EVA Airways Corp.", "TWSE", "Taiwan", "Industrials", "Airlines", "large", "TWD", "Major international airline"),
    "2633": Stock("2633", "Taiwan High Speed Rail Corp.", "TWSE", "Taiwan", "Industrials", "Railways", "large", "TWD", "High-speed rail transportation company"),

    # === FOOD & BEVERAGES ===
    "1216": Stock("1216", "Uni-President Enterprises Corp.", "TWSE", "Taiwan", "Consumer Staples", "Food Products", "large", "TWD", "Leading food and beverage company"),
    "1201": Stock("1201", "Wei Chuan Foods Corp.", "TWSE", "Taiwan", "Consumer Staples", "Food Products", "large", "TWD", "Food processing company"),
    "1229": Stock("1229", "Lien Hwa Industrial Holdings Corp.", "TWSE", "Taiwan", "Consumer Staples", "Food Products", "large", "TWD", "Food manufacturing holding company"),

    # === RETAIL & CONSUMER SERVICES ===
    "2912": Stock("2912", "President Chain Store Corp.", "TWSE", "Taiwan", "Consumer Discretionary", "Retail", "large", "TWD", "Convenience store operator (7-Eleven Taiwan)"),
    "2903": Stock("2903", "Far Eastern Department Stores Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Retail", "large", "TWD", "Department store and retail company"),
    "2915": Stock("2915", "Ruentex Industries Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Retail", "large", "TWD", "Retail and department store company"),
    "8454": Stock("8454", "MoMo.com Inc.", "TWSE", "Taiwan", "Consumer Discretionary", "E-commerce", "large", "TWD", "Leading e-commerce and TV shopping company"),

    # === CONSTRUCTION & REAL ESTATE ===
    "2501": Stock("2501", "Cathay Real Estate Development Co., Ltd.", "TWSE", "Taiwan", "Real Estate", "Real Estate Development", "large", "TWD", "Real estate development company"),
    "5522": Stock("5522", "Farglory Land Development Co., Ltd.", "TWSE", "Taiwan", "Real Estate", "Real Estate Development", "large", "TWD", "Real estate development and construction company"),
    "9940": Stock("9940", "Sinyi Realty Inc.", "TWSE", "Taiwan", "Real Estate", "Real Estate Services", "large", "TWD", "Leading real estate services company"),

    # === TEXTILES & APPAREL ===
    "1476": Stock("1476", "Eclat Textile Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Textiles", "large", "TWD", "Athletic and outdoor apparel manufacturer"),
    "1477": Stock("1477", "Makalot Industrial Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Textiles", "large", "TWD", "Garment manufacturing company"),
    "9904": Stock("9904", "Pou Chen Corp.", "TWSE", "Taiwan", "Consumer Discretionary", "Footwear", "large", "TWD", "World's largest athletic and casual footwear manufacturer"),
    "9910": Stock("9910", "Feng Tay Enterprise Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Footwear", "large", "TWD", "Athletic footwear manufacturer"),

    # === MACHINERY & INDUSTRIAL ===
    "9921": Stock("9921", "Giant Manufacturing Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Bicycles", "large", "TWD", "Leading bicycle manufacturer"),
    "9914": Stock("9914", "Merida Industry Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Bicycles", "large", "TWD", "Bicycle manufacturer"),
    "1590": Stock("1590", "Airtac International Group", "TWSE", "Taiwan", "Industrials", "Industrial Automation", "large", "TWD", "Pneumatic equipment manufacturer"),

    # === HEALTHCARE & BIOTECHNOLOGY ===
    "1707": Stock("1707", "Grape King Bio Ltd.", "TWSE", "Taiwan", "Healthcare", "Biotechnology", "large", "TWD", "Biotechnology and health food company"),
    "6446": Stock("6446", "PharmaEssentia Corp.", "TWSE", "Taiwan", "Healthcare", "Pharmaceuticals", "large", "TWD", "Biopharmaceutical company"),
    "4142": Stock("4142", "Adimmune Corp.", "TWSE", "Taiwan", "Healthcare", "Biotechnology", "large", "TWD", "Vaccine and biotechnology company"),

    # === UTILITIES & ENERGY ===
    "9908": Stock("9908", "Great Taipei Gas Co., Ltd.", "TWSE", "Taiwan", "Utilities", "Gas Utilities", "large", "TWD", "Natural gas distribution company"),
    "9918": Stock("9918", "Shin Shin Natural Gas Co., Ltd.", "TWSE", "Taiwan", "Utilities", "Gas Utilities", "large", "TWD", "Natural gas utility company"),

    # === PAPER & PACKAGING ===
    "1904": Stock("1904", "Cheng Loong Corp.", "TWSE", "Taiwan", "Materials", "Paper Products", "large", "TWD", "Paper and packaging manufacturer"),
    "1905": Stock("1905", "Chung Hwa Pulp Corp.", "TWSE", "Taiwan", "Materials", "Paper Products", "large", "TWD", "Pulp and paper manufacturer"),

    # === GLASS & BUILDING MATERIALS ===
    "1802": Stock("1802", "Taiwan Glass Ind. Corp.", "TWSE", "Taiwan", "Materials", "Glass", "large", "TWD", "Glass manufacturing company"),
    "1101": Stock("1101", "TCC Group Holdings Co., Ltd.", "TWSE", "Taiwan", "Materials", "Cement", "large", "TWD", "Cement manufacturing company"),
    "1102": Stock("1102", "Asia Cement Corp.", "TWSE", "Taiwan", "Materials", "Cement", "large", "TWD", "Cement and building materials company"),

    # === AUTOMOTIVE ===
    "2201": Stock("2201", "Yulon Motor Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Automotive", "large", "TWD", "Automotive manufacturer and distributor"),
    "2207": Stock("2207", "Hotai Motor Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Automotive", "large", "TWD", "Toyota distributor and automotive services"),
    "2227": Stock("2227", "Yulon Nissan Motor Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Automotive", "large", "TWD", "Nissan distributor in Taiwan"),

    # === RUBBER & TIRES ===
    "2105": Stock("2105", "Cheng Shin Rubber Ind. Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Tires", "large", "TWD", "Tire and rubber products manufacturer"),
    "2101": Stock("2101", "Nan Kang Rubber Tire Co., Ltd.", "TWSE", "Taiwan", "Consumer Discretionary", "Tires", "large", "TWD", "Tire manufacturer"),

    # === SPECIALTY COMPANIES ===
    "2727": Stock("2727", "WowPrime Corp.", "TWSE", "Taiwan", "Consumer Discretionary", "Restaurants", "large", "TWD", "Restaurant chain operator"),
    "9933": Stock("9933", "CTCI Corp.", "TWSE", "Taiwan", "Industrials", "Engineering Services", "large", "TWD", "Engineering and construction services"),
    "9917": Stock("9917", "Taiwan Secom Co., Ltd.", "TWSE", "Taiwan", "Industrials", "Security Services", "large", "TWD", "Security services company"),
}
