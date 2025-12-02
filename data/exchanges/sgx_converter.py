#!/usr/bin/env python3
"""
Script to convert SGX IB mapping data to SGX stocks database format.
This script reads from sgx_ib_map.csv and generates an updated sgx_stocks.py file
with comprehensive stock listings.
"""

import csv
import os
import re
from collections import defaultdict

# Define sectors and industries based on common patterns in company names
SECTOR_MAPPINGS = {
    r'BANK|FINANCIAL|CAPITAL|INVEST|ASSET|INSURANCE': ('Financials', 'Banking & Financial Services'),
    r'TELECOM|COMMUNICATION|MEDIA|ENTERTAINMENT': ('Communication Services', 'Telecommunications'),
    r'REAL ESTATE|PROPERTY|LAND|DEVELOPMENT|REIT': ('Real Estate', 'Real Estate'),
    r'TECH|ELECTRONIC|SEMICONDUCTOR|SOFTWARE|DIGITAL': ('Technology', 'Technology'),
    r'AIRLINE|SHIPPING|TRANSPORT|LOGISTIC|MARINE': ('Industrials', 'Transportation'),
    r'FOOD|BEVERAGE|RESTAURANT|RETAIL|CONSUMER': ('Consumer Discretionary', 'Consumer Products'),
    r'HEALTHCARE|MEDICAL|PHARMA|HOSPITAL': ('Healthcare', 'Healthcare'),
    r'OIL|GAS|ENERGY|POWER': ('Energy', 'Energy'),
    r'ENGINEERING|CONSTRUCTION|INDUSTRIAL|MANUFACTURING': ('Industrials', 'Manufacturing'),
    r'HOTEL|HOSPITALITY|RESORT|TRAVEL|TOURISM': ('Consumer Discretionary', 'Hospitality'),
    r'AGRICULTURE|PLANTATION|RESOURCE': ('Materials', 'Agriculture'),
}

# REIT detection
REIT_PATTERN = r'REIT|TRUST|COMMERCIAL TRUST|INDUSTRIAL TRUST|HOSPITALITY TRUST'

# Skip these symbols as they're not regular stocks
SKIP_PATTERNS = [
    r'^[A-Z]\d{2}$',  # Futures contract patterns
    r'FUTURES',
    r'INDEX',
    r'ACCEPTANCE',
    r'SOCIETE GENERALE',
    r'WARRANT',
]

# Known major stocks to ensure they're included
MAJOR_STOCKS = {
    'D05': 'DBS Group Holdings Ltd',
    'O39': 'Oversea-Chinese Banking Corp',
    'U11': 'United Overseas Bank Ltd',
    'C6L': 'Singapore Airlines Ltd',
    'Z74': 'Singapore Telecommunications Ltd',
    'S68': 'Singapore Exchange Ltd',
    'C38U': 'CapitaLand Integrated Commercial Trust',
    'C52': 'ComfortDelGro Corp Ltd',
    'F34': 'Wilmar International Ltd',
    'S63': 'Singapore Technologies Engineering Ltd',
}

def determine_sector_industry(company_name):
    """Determine sector and industry based on company name"""
    company_name_upper = company_name.upper()
    
    # Check for REITs first
    if re.search(REIT_PATTERN, company_name_upper):
        return 'Real Estate', 'REITs'
    
    # Check other sector mappings
    for pattern, (sector, industry) in SECTOR_MAPPINGS.items():
        if re.search(pattern, company_name_upper):
            return sector, industry
    
    # Default if no match
    return 'Industrials', 'Diversified'

def determine_size(symbol, description):
    """Determine company size based on symbol and description"""
    # Major stocks are large cap
    if symbol in MAJOR_STOCKS:
        return 'large'
    
    # REITs are typically mid to large
    if 'REIT' in description or 'Trust' in description:
        return 'mid'
    
    # Simple heuristic based on symbol length
    if len(symbol) <= 3:
        return 'large'
    elif len(symbol) == 4:
        return 'mid'
    else:
        return 'small'

def should_skip(symbol, description):
    """Determine if this symbol should be skipped"""
    # Check against skip patterns
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, description):
            return True
    
    # Allow alphanumeric symbols with basic punctuation
    if not re.match(r'^[A-Z0-9\.\-]+$', symbol):
        return True
        
    return False

def clean_symbol(symbol):
    """Clean and format the symbol for SGX"""
    # Remove any futures contract suffixes
    symbol = re.sub(r'[A-Z]\d{2}$', '', symbol)
    
    # Add .SI suffix for SGX stocks
    return f"{symbol}.SI"

def generate_description(company_name, sector, industry):
    """Generate a simple description based on company name and sector"""
    if 'REIT' in company_name or 'Trust' in company_name:
        return f"Real estate investment trust focused on {industry.lower()} properties"
    
    industry_lower = industry.lower()
    if sector == 'Financials':
        return f"Financial services provider in {industry_lower}"
    elif sector == 'Technology':
        return f"Technology company specializing in {industry_lower}"
    elif sector == 'Consumer Discretionary':
        return f"{industry} company in Singapore"
    elif sector == 'Industrials':
        return f"{industry} services and solutions provider"
    elif sector == 'Healthcare':
        return f"Healthcare and {industry_lower} services"
    elif sector == 'Energy':
        return f"Energy and {industry_lower} company"
    else:
        return f"{industry} company based in Singapore"

def main():
    # Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, 'sgx_ib_map.csv')
    output_file = os.path.join(current_dir, 'sgx_stocks.py')
    
    # Read the CSV file
    stocks = {}
    seen_symbols = set()
    
    with open(input_file, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t')
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) < 6:
                continue
                
            symbol, description, ib_symbol, currency, region, exchange = row[:6]
            
            # Skip non-SGX or non-stock entries
            if exchange != 'SGX' or currency not in ['SGD', 'USD']:
                continue
                
            # Skip derivatives, indices, etc.
            if should_skip(symbol, description):
                continue
                
            # Clean symbol
            clean_sym = clean_symbol(symbol)
            if clean_sym in seen_symbols:
                continue
                
            seen_symbols.add(clean_sym)
            
            # Determine sector and industry
            sector, industry = determine_sector_industry(description)
            
            # Determine size
            size = determine_size(symbol, description)
            
            # Generate description
            desc = generate_description(description, sector, industry)
            
            # Create stock entry
            stocks[clean_sym] = {
                'symbol': clean_sym,
                'name': description,
                'sector': sector,
                'industry': industry,
                'size': size,
                'description': desc
            }
    
    # Add any missing major stocks
    for symbol, name in MAJOR_STOCKS.items():
        clean_sym = clean_symbol(symbol)
        if clean_sym not in stocks:
            sector, industry = determine_sector_industry(name)
            stocks[clean_sym] = {
                'symbol': clean_sym,
                'name': name,
                'sector': sector,
                'industry': industry,
                'size': 'large',
                'description': generate_description(name, sector, industry)
            }
    
    # Group stocks by sector for better organization
    sectors = defaultdict(list)
    for symbol, stock in stocks.items():
        sectors[stock['sector']].append((symbol, stock))
    
    # Generate the Python file
    with open(output_file, 'w') as pyfile:
        pyfile.write('"""')
        pyfile.write('Singapore Exchange (SGX) stocks database.\n')
        pyfile.write('Contains stocks listed on the Singapore Stock Exchange.\n')
        pyfile.write('Auto-generated from sgx_ib_map.csv\n')
        pyfile.write('"""\n\n')
        pyfile.write('from ..models import Stock\n\n')
        pyfile.write('# Singapore Exchange (SGX) Stocks\n')
        pyfile.write('SGX_STOCKS = {\n')
        
        for sector, stock_list in sectors.items():
            pyfile.write(f"    # {sector}\n")
            for symbol, stock in sorted(stock_list):
                stock_str = f'    "{symbol}": Stock("{symbol}", "{stock["name"]}", "SGX", "Singapore", "{stock["sector"]}", "{stock["industry"]}", "{stock["size"]}", "SGD", "{stock["description"]}"),\n'
                pyfile.write(stock_str)
            pyfile.write('\n')
        
        pyfile.write('}\n')
    
    print(f"Generated {len(stocks)} stock entries in {output_file}")

if __name__ == "__main__":
    main()
