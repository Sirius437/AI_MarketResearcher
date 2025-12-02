"""
Korea Stock Exchange (KSE) to Interactive Brokers symbol mapper.

This module provides mapping functionality between Korea Stock Exchange symbols and 
Interactive Brokers symbols for trading and data retrieval.
"""

import csv
import os
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class KSEIBMapper:
    """Maps Korea Stock Exchange symbols to Interactive Brokers symbols."""
    
    def __init__(self):
        """Initialize the mapper with KSE symbol data."""
        self.symbol_map = {}
        self.reverse_map = {}
        self.symbol_info = {}
        self._load_symbols()
    
    def _load_symbols(self):
        """Load KSE symbols from CSV file."""
        try:
            csv_path = os.path.join(
                os.path.dirname(__file__), 
                'exchanges', 
                'kse_ib_map.csv'
            )
            
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Use tab separator and handle the header
                reader = csv.DictReader(file, delimiter='\t')
                
                for row in reader:
                    # Clean column names (remove extra spaces)
                    cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
                    
                    kse_symbol = cleaned_row.get('SYMBOL', '').strip()
                    ib_symbol = cleaned_row.get('IBKR SYMBOL', '').strip()
                    description = cleaned_row.get('DESCRIPTION', '').strip()
                    currency = cleaned_row.get('CURRENCY', 'KRW').strip()
                    region = cleaned_row.get('REGION', 'KR').strip()
                    exchange = cleaned_row.get('EXCHANGE', 'KSE').strip()
                    
                    if kse_symbol and ib_symbol:
                        # Handle multiple IB symbols for same KSE symbol (use first one as primary)
                        if kse_symbol not in self.symbol_map:
                            self.symbol_map[kse_symbol] = ib_symbol
                            
                            # Store detailed info
                            self.symbol_info[kse_symbol] = {
                                'ib_symbol': ib_symbol,
                                'description': description,
                                'currency': currency,
                                'region': region,
                                'exchange': exchange,
                                'alternate_symbols': []
                            }
                        else:
                            # Add alternate IB symbols
                            self.symbol_info[kse_symbol]['alternate_symbols'].append(ib_symbol)
                        
                        # Reverse mapping: IB -> KSE
                        self.reverse_map[ib_symbol] = kse_symbol
            
            logger.info(f"Loaded {len(self.symbol_map)} KSE symbols")
            
        except FileNotFoundError:
            logger.error("KSE IB mapping file not found")
        except Exception as e:
            logger.error(f"Error loading KSE symbols: {e}")
    
    def get_ib_symbol(self, kse_symbol: str) -> Optional[str]:
        """Get Interactive Brokers symbol for a KSE symbol."""
        return self.symbol_map.get(kse_symbol.upper())
    
    def get_kse_symbol(self, ib_symbol: str) -> Optional[str]:
        """Get KSE symbol for an Interactive Brokers symbol."""
        return self.reverse_map.get(ib_symbol.upper())
    
    def get_symbol_info(self, kse_symbol: str) -> Optional[Dict[str, str]]:
        """Get detailed information for a KSE symbol."""
        return self.symbol_info.get(kse_symbol.upper())
    
    def get_all_ib_symbols(self, kse_symbol: str) -> List[str]:
        """Get all IB symbols (primary + alternates) for a KSE symbol."""
        info = self.get_symbol_info(kse_symbol)
        if not info:
            return []
        
        symbols = [info['ib_symbol']]
        symbols.extend(info.get('alternate_symbols', []))
        return symbols
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search KSE symbols by name or description."""
        query = query.upper()
        results = []
        
        for symbol, info in self.symbol_info.items():
            if (query in symbol or 
                query in info['description'].upper()):
                results.append({
                    'kse_symbol': symbol,
                    'ib_symbol': info['ib_symbol'],
                    'description': info['description'],
                    'currency': info['currency'],
                    'alternates': len(info.get('alternate_symbols', []))
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_symbols(self) -> List[str]:
        """Get all KSE symbols."""
        return list(self.symbol_map.keys())
    
    def get_contract_details(self, kse_symbol: str) -> Optional[Dict[str, Any]]:
        """Get contract details for Interactive Brokers API."""
        info = self.get_symbol_info(kse_symbol)
        if not info:
            return None
        
        return {
            'symbol': info['ib_symbol'],
            'secType': 'STK',
            'exchange': 'KSE',
            'currency': info['currency'],
            'localSymbol': info['ib_symbol']
        }

# Global instance
kse_mapper = KSEIBMapper()

def main():
    """Test the KSE mapper functionality."""
    print("KSE-IB Mapper Test")
    print("=" * 50)
    
    # Test symbol mappings
    print("\nTesting symbol mappings:")
    test_symbols = ['000080', '000100', '005930', '000660', '035720', '051910']
    
    for symbol in test_symbols:
        ib_symbol = kse_mapper.get_ib_symbol(symbol)
        info = kse_mapper.get_symbol_info(symbol)
        if ib_symbol and info:
            alternates = len(info.get('alternate_symbols', []))
            print(f"KSE {symbol} -> IB {ib_symbol} ({info['description'][:40]}...)")
            if alternates > 0:
                print(f"   + {alternates} alternate IB symbols")
        else:
            print(f"KSE {symbol} -> No mapping found")
    
    print(f"\nTotal symbols loaded: {len(kse_mapper.get_all_symbols())}")
    
    # Test search functionality
    print("\nSearch results for 'SAMSUNG':")
    samsung_results = kse_mapper.search_symbols('SAMSUNG', 3)
    for result in samsung_results:
        print(f"  {result['kse_symbol']}: {result['description']}")
    
    print("\nSearch results for 'LG':")
    lg_results = kse_mapper.search_symbols('LG', 3)
    for result in lg_results:
        print(f"  {result['kse_symbol']}: {result['description']}")

if __name__ == "__main__":
    main()
