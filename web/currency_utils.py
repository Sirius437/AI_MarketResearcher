"""
Currency utilities for web interface display formatting.
"""

def get_currency_symbol(currency_code: str) -> str:
    """
    Get currency symbol for display formatting.
    
    Args:
        currency_code: ISO currency code (e.g., 'USD', 'MYR', 'EUR')
        
    Returns:
        Currency symbol string
    """
    currency_map = {
        # Major currencies
        'USD': '$',   # US Dollar
        'EUR': '€',   # Euro
        'GBP': '£',   # British Pound
        'JPY': '¥',   # Japanese Yen
        'CHF': 'CHF ', # Swiss Franc
        'CAD': 'C$',  # Canadian Dollar
        'AUD': 'A$',  # Australian Dollar
        'NZD': 'NZ$', # New Zealand Dollar
        
        # Asian currencies
        'CNY': '¥',   # Chinese Yuan
        'HKD': 'HK$', # Hong Kong Dollar
        'SGD': 'S$',  # Singapore Dollar
        'KRW': '₩',   # South Korean Won
        'INR': '₹',   # Indian Rupee
        'IDR': 'Rp',  # Indonesian Rupiah
        'THB': '฿',   # Thai Baht
        'MYR': 'RM',  # Malaysian Ringgit
        'PHP': '₱',   # Philippine Peso
        'VND': '₫',   # Vietnamese Dong
        'TWD': 'NT$', # Taiwan Dollar
        
        # European currencies
        'SEK': 'kr',  # Swedish Krona
        'NOK': 'kr',  # Norwegian Krone
        'DKK': 'kr',  # Danish Krone
        'PLN': 'zł',  # Polish Zloty
        'CZK': 'Kč',  # Czech Koruna
        'HUF': 'Ft',  # Hungarian Forint
        'RUB': '₽',   # Russian Ruble
        
        # Middle East & Africa
        'SAR': 'SR',  # Saudi Riyal
        'AED': 'د.إ', # UAE Dirham
        'EGP': 'E£',  # Egyptian Pound
        'ZAR': 'R',   # South African Rand
        'ILS': '₪',   # Israeli Shekel
        'TRY': '₺',   # Turkish Lira
        
        # Americas
        'BRL': 'R$',  # Brazilian Real
        'MXN': '$',   # Mexican Peso
        'ARS': '$',   # Argentine Peso
        'CLP': '$',   # Chilean Peso
        'COP': '$',   # Colombian Peso
        'PEN': 'S/',  # Peruvian Sol
    }
    
    return currency_map.get(currency_code, currency_code + ' ')

def get_stock_currency(symbol: str) -> str:
    """
    Get currency for a stock symbol by looking up in stocks database.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Currency code (e.g., 'USD', 'MYR')
    """
    try:
        from data.stocks_database import StocksDatabase
        stocks_db = StocksDatabase()
        stock_info = stocks_db.get_stock_by_symbol(symbol)
        if stock_info and stock_info.currency:
            return stock_info.currency
    except Exception:
        pass
    
    # Default to USD if not found
    return 'USD'

def format_currency(amount: float, symbol: str) -> str:
    """
    Format currency amount with appropriate symbol.
    
    Args:
        amount: Numeric amount
        symbol: Stock symbol to determine currency
        
    Returns:
        Formatted currency string
    """
    currency_code = get_stock_currency(symbol)
    currency_symbol = get_currency_symbol(currency_code)
    
    return f"{currency_symbol}{amount:.2f}"
