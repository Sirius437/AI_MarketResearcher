"""
Tokyo Stock Exchange (TSEJ) to Interactive Brokers symbol mapper.

This module provides mapping functionality between Tokyo Stock Exchange symbols and 
Interactive Brokers symbols for trading and data retrieval.
"""

import csv
import os
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class TSEJIBMapper:
    """Maps Tokyo Stock Exchange symbols to Interactive Brokers symbols."""
    
    def __init__(self):
        """Initialize the mapper with TSEJ symbol data."""
        self.symbol_map = {}
        self.reverse_map = {}
        self.symbol_info = {}
        self._load_symbols()
    
    def _load_symbols(self):
        """Load TSEJ symbols from CSV file."""
        try:
            csv_path = os.path.join(
                os.path.dirname(__file__), 
                'exchanges', 
                'TSEJ_ib_map.csv'
            )
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Use tab separator and handle the header
                reader = csv.DictReader(file, delimiter='\t')
                
                for row in reader:
                    # Clean column names (remove extra spaces)
                    cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                    
                    tsej_symbol = cleaned_row.get('SYMBOL', '').strip()
                    ib_symbol = cleaned_row.get('IBKR SYMBOL', '').strip()
                    description = cleaned_row.get('DESCRIPTION', '').strip()
                    currency = cleaned_row.get('CURRENCY', 'JPY').strip()
                    region = cleaned_row.get('REGION', 'JP').strip()
                    exchange = cleaned_row.get('EXCHANGE', 'TSEJ').strip()
                    
                    if tsej_symbol and ib_symbol:
                        # Forward mapping: TSEJ -> IB
                        self.symbol_map[tsej_symbol] = ib_symbol
                        
                        # Reverse mapping: IB -> TSEJ
                        self.reverse_map[ib_symbol] = tsej_symbol
                        
                        # Store detailed info
                        self.symbol_info[tsej_symbol] = {
                            'ib_symbol': ib_symbol,
                            'description': description,
                            'currency': currency,
                            'region': region,
                            'exchange': exchange
                        }
            
            logger.info(f"Loaded {len(self.symbol_map)} TSEJ symbols")
            
        except FileNotFoundError:
            logger.error("TSEJ IB mapping file not found")
        except Exception as e:
            logger.error(f"Error loading TSEJ symbols: {e}")
    
    def get_ib_symbol(self, tsej_symbol: str) -> Optional[str]:
        """Get Interactive Brokers symbol for a TSEJ symbol."""
        return self.symbol_map.get(tsej_symbol.upper())
    
    def get_tsej_symbol(self, ib_symbol: str) -> Optional[str]:
        """Get TSEJ symbol for an Interactive Brokers symbol."""
        return self.reverse_map.get(ib_symbol.upper())
    
    def get_symbol_info(self, tsej_symbol: str) -> Optional[Dict[str, str]]:
        """Get detailed information for a TSEJ symbol."""
        return self.symbol_info.get(tsej_symbol.upper())
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search TSEJ symbols by name or description."""
        query = query.upper()
        results = []
        
        for symbol, info in self.symbol_info.items():
            if (query in symbol or 
                query in info['description'].upper()):
                results.append({
                    'tsej_symbol': symbol,
                    'ib_symbol': info['ib_symbol'],
                    'description': info['description'],
                    'currency': info['currency']
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_symbols(self) -> List[str]:
        """Get all TSEJ symbols."""
        return list(self.symbol_map.keys())
    
    def get_contract_details(self, tsej_symbol: str) -> Optional[Dict[str, Any]]:
        """Get contract details for Interactive Brokers API."""
        info = self.get_symbol_info(tsej_symbol)
        if not info:
            return None
        
        return {
            'symbol': info['ib_symbol'],
            'secType': 'STK',
            'exchange': 'TSEJ',
            'currency': info['currency'],
            'localSymbol': info['ib_symbol']
        }

# Global instance
tsej_mapper = TSEJIBMapper()

def main():
    """Test the TSEJ mapper functionality."""
    print("TSEJ-IB Mapper Test")
    print("=" * 50)
    
    # Test symbol mappings
    print("\nTesting symbol mappings:")
    test_symbols = ['1301', '7203', '6758', '9984', '8306', '4519']
    
    for symbol in test_symbols:
        ib_symbol = tsej_mapper.get_ib_symbol(symbol)
        info = tsej_mapper.get_symbol_info(symbol)
        if ib_symbol and info:
            print(f"TSEJ {symbol} -> IB {ib_symbol} ({info['description'][:40]}...)")
        else:
            print(f"TSEJ {symbol} -> No mapping found")
    
    print(f"\nTotal symbols loaded: {len(tsej_mapper.get_all_symbols())}")
    
    # Test search functionality
    print("\nSearch results for 'TOYOTA':")
    toyota_results = tsej_mapper.search_symbols('TOYOTA', 3)
    for result in toyota_results:
        print(f"  {result['tsej_symbol']}: {result['description']}")
    
    print("\nSearch results for 'SONY':")
    sony_results = tsej_mapper.search_symbols('SONY', 3)
    for result in sony_results:
        print(f"  {result['tsej_symbol']}: {result['description']}")

if __name__ == "__main__":
    main()
