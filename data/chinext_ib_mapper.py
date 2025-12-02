"""
ChiNext (Shenzhen Growth Enterprise Market) to Interactive Brokers symbol mapper.

This module provides mapping functionality between ChiNext stock symbols and 
Interactive Brokers symbols for trading and data retrieval.
"""

import csv
import os
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ChiNextIBMapper:
    """Maps ChiNext symbols to Interactive Brokers symbols."""
    
    def __init__(self):
        """Initialize the mapper with ChiNext symbol data."""
        self.symbol_map = {}
        self.reverse_map = {}
        self.symbol_info = {}
        self._load_symbols()
    
    def _load_symbols(self):
        """Load ChiNext symbols from CSV file."""
        try:
            csv_path = os.path.join(
                os.path.dirname(__file__), 
                'exchanges', 
                'chinext_ib_map.csv'
            )
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Use tab separator and handle the header
                reader = csv.DictReader(file, delimiter='\t')
                
                for row in reader:
                    # Clean column names (remove extra spaces)
                    cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                    
                    chinext_symbol = cleaned_row.get('SYMBOL', '').strip()
                    ib_symbol = cleaned_row.get('IBKR SYMBOL', '').strip()
                    description = cleaned_row.get('DESCRIPTION', '').strip()
                    currency = cleaned_row.get('CURRENCY', 'CNH').strip()
                    region = cleaned_row.get('REGION', 'HK').strip()
                    exchange = cleaned_row.get('EXCHANGE', 'CHINEXT').strip()
                    
                    if chinext_symbol and ib_symbol:
                        # Forward mapping: ChiNext -> IB
                        self.symbol_map[chinext_symbol] = ib_symbol
                        
                        # Reverse mapping: IB -> ChiNext
                        self.reverse_map[ib_symbol] = chinext_symbol
                        
                        # Store detailed info
                        self.symbol_info[chinext_symbol] = {
                            'ib_symbol': ib_symbol,
                            'description': description,
                            'currency': currency,
                            'region': region,
                            'exchange': exchange
                        }
            
            logger.info(f"Loaded {len(self.symbol_map)} ChiNext symbols")
            
        except FileNotFoundError:
            logger.error("ChiNext IB mapping file not found")
        except Exception as e:
            logger.error(f"Error loading ChiNext symbols: {e}")
    
    def get_ib_symbol(self, chinext_symbol: str) -> Optional[str]:
        """Get Interactive Brokers symbol for a ChiNext symbol."""
        return self.symbol_map.get(chinext_symbol.upper())
    
    def get_chinext_symbol(self, ib_symbol: str) -> Optional[str]:
        """Get ChiNext symbol for an Interactive Brokers symbol."""
        return self.reverse_map.get(ib_symbol.upper())
    
    def get_symbol_info(self, chinext_symbol: str) -> Optional[Dict[str, str]]:
        """Get detailed information for a ChiNext symbol."""
        return self.symbol_info.get(chinext_symbol.upper())
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search ChiNext symbols by name or description."""
        query = query.upper()
        results = []
        
        for symbol, info in self.symbol_info.items():
            if (query in symbol or 
                query in info['description'].upper()):
                results.append({
                    'chinext_symbol': symbol,
                    'ib_symbol': info['ib_symbol'],
                    'description': info['description'],
                    'currency': info['currency']
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_symbols(self) -> List[str]:
        """Get all ChiNext symbols."""
        return list(self.symbol_map.keys())
    
    def get_contract_details(self, chinext_symbol: str) -> Optional[Dict[str, Any]]:
        """Get contract details for Interactive Brokers API."""
        info = self.get_symbol_info(chinext_symbol)
        if not info:
            return None
        
        return {
            'symbol': info['ib_symbol'],
            'secType': 'STK',
            'exchange': 'CHINEXT',
            'currency': info['currency'],
            'localSymbol': info['ib_symbol']
        }

# Global instance
chinext_mapper = ChiNextIBMapper()

def main():
    """Test the ChiNext mapper functionality."""
    print("ChiNext-IB Mapper Test")
    print("=" * 50)
    
    # Test symbol mappings
    print("\nTesting symbol mappings:")
    test_symbols = ['300001', '300002', '300003', '300750', '301516', '301658']
    
    for symbol in test_symbols:
        ib_symbol = chinext_mapper.get_ib_symbol(symbol)
        info = chinext_mapper.get_symbol_info(symbol)
        if ib_symbol and info:
            print(f"ChiNext {symbol} -> IB {ib_symbol} ({info['description'][:40]}...)")
        else:
            print(f"ChiNext {symbol} -> No mapping found")
    
    print(f"\nTotal symbols loaded: {len(chinext_mapper.get_all_symbols())}")
    
    # Test search functionality
    print("\nSearch results for 'TECHNOLOGY':")
    tech_results = chinext_mapper.search_symbols('TECHNOLOGY', 3)
    for result in tech_results:
        print(f"  {result['chinext_symbol']}: {result['description']}")
    
    print("\nSearch results for 'MEDICAL':")
    medical_results = chinext_mapper.search_symbols('MEDICAL', 3)
    for result in medical_results:
        print(f"  {result['chinext_symbol']}: {result['description']}")

if __name__ == "__main__":
    main()
