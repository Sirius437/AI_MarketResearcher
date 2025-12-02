"""
Saudi Stock Exchange (Tadawul) - Saudi Arabia stocks.
"""

from ..models import Stock

# Saudi Arabia stocks
TADAWUL_STOCKS = {
    # Saudi Arabia - Energy
    "2222.SR": Stock("2222.SR", "Saudi Aramco", "TADAWUL", "Saudi Arabia", "Energy", "Oil & Gas", "large", "SAR", "Saudi Arabian state-owned petroleum and natural gas company"),
    "2030.SR": Stock("2030.SR", "Saudi Electricity Company", "TADAWUL", "Saudi Arabia", "Utilities", "Electric Utilities", "large", "SAR", "Saudi Arabian electric utility company"),
    
    # Saudi Arabia - Banking
    "1180.SR": Stock("1180.SR", "Al Rajhi Bank", "TADAWUL", "Saudi Arabia", "Financials", "Islamic Banking", "large", "SAR", "Saudi Arabian Islamic bank"),
    "1120.SR": Stock("1120.SR", "National Commercial Bank", "TADAWUL", "Saudi Arabia", "Financials", "Banking", "large", "SAR", "Saudi Arabian commercial bank"),
    "1010.SR": Stock("1010.SR", "Riyad Bank", "TADAWUL", "Saudi Arabia", "Financials", "Banking", "large", "SAR", "Saudi Arabian bank"),
    
    # Saudi Arabia - Petrochemicals
    "2010.SR": Stock("2010.SR", "Saudi Basic Industries Corporation", "TADAWUL", "Saudi Arabia", "Materials", "Chemicals", "large", "SAR", "Saudi Arabian chemical manufacturing company"),
    "2350.SR": Stock("2350.SR", "Saudi Kayan Petrochemical Company", "TADAWUL", "Saudi Arabia", "Materials", "Chemicals", "large", "SAR", "Saudi Arabian petrochemical company"),
    
    # Saudi Arabia - Telecommunications
    "7010.SR": Stock("7010.SR", "Saudi Telecom Company", "TADAWUL", "Saudi Arabia", "Communication Services", "Telecommunications", "large", "SAR", "Saudi Arabian telecommunications company"),
    "7020.SR": Stock("7020.SR", "Etihad Etisalat Company", "TADAWUL", "Saudi Arabia", "Communication Services", "Telecommunications", "large", "SAR", "Saudi Arabian mobile telecommunications company"),
    
    # Saudi Arabia - Healthcare
    "4004.SR": Stock("4004.SR", "Dr. Sulaiman Al Habib Medical Services Group", "TADAWUL", "Saudi Arabia", "Healthcare", "Medical Services", "large", "SAR", "Saudi Arabian healthcare provider"),
}
