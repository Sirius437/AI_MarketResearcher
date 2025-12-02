#!/usr/bin/env python3
"""
SEHKSTAR (Shanghai Stock Exchange via Hong Kong) to Interactive Brokers Symbol Mapper

This module provides mapping functionality between Shanghai Stock Exchange stocks 
(traded via Hong Kong Connect) and their corresponding Interactive Brokers symbols.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class SEHKSTARIBMapper:
    """Maps SEHKSTAR symbols to Interactive Brokers symbols."""
    
    def __init__(self):
        self.mapping_file = Path(__file__).parent / "exchanges" / "sehkstar_ib_map.csv"
        self.symbol_map = {}
        self.reverse_map = {}
        self.load_mappings()
    
    def load_mappings(self):
        """Load SEHKSTAR to IB symbol mappings from CSV file."""
        try:
            if not self.mapping_file.exists():
                logger.error(f"SEHKSTAR mapping file not found: {self.mapping_file}")
                return
            
            df = pd.read_csv(self.mapping_file, sep='\t', on_bad_lines='skip')
            logger.info(f"Loaded {len(df)} SEHKSTAR-IB mappings")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Create symbol mappings
            for _, row in df.iterrows():
                sehkstar_symbol = str(row['SYMBOL']).strip()
                ib_symbol = str(row['IBKR SYMBOL']).strip()
                description = str(row.get('DESCRIPTION', '')).strip()
                currency = str(row.get('CURRENCY', 'CNH')).strip()
                
                # Skip invalid entries
                if not sehkstar_symbol or sehkstar_symbol == 'nan' or not ib_symbol or ib_symbol == 'nan':
                    continue
                
                # Primary mapping: SEHKSTAR symbol -> IB symbol
                if sehkstar_symbol not in self.symbol_map:
                    self.symbol_map[sehkstar_symbol] = {
                        'ib_symbol': ib_symbol,
                        'description': description,
                        'currency': currency,
                        'exchange': 'SEHKSTAR'
                    }
                
                # Reverse mapping for lookups
                self.reverse_map[ib_symbol] = sehkstar_symbol
            
            logger.info(f"Successfully loaded {len(self.symbol_map)} unique SEHKSTAR symbols")
            
        except Exception as e:
            logger.error(f"Error loading SEHKSTAR mappings: {e}")
    
    def get_ib_symbol(self, sehkstar_symbol: str) -> Optional[str]:
        """Get Interactive Brokers symbol for a SEHKSTAR symbol."""
        sehkstar_symbol = str(sehkstar_symbol).strip()
        mapping = self.symbol_map.get(sehkstar_symbol)
        return mapping['ib_symbol'] if mapping else None
    
    def get_sehkstar_symbol(self, ib_symbol: str) -> Optional[str]:
        """Get SEHKSTAR symbol from Interactive Brokers symbol."""
        return self.reverse_map.get(str(ib_symbol).strip())
    
    def get_symbol_info(self, sehkstar_symbol: str) -> Optional[Dict]:
        """Get complete symbol information."""
        return self.symbol_map.get(str(sehkstar_symbol).strip())
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for symbols by name or symbol."""
        query = query.lower().strip()
        results = []
        
        for symbol, info in self.symbol_map.items():
            if (query in symbol.lower() or 
                query in info.get('description', '').lower()):
                results.append({
                    'sehkstar_symbol': symbol,
                    'ib_symbol': info['ib_symbol'],
                    'description': info['description'],
                    'currency': info['currency']
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_symbols(self) -> List[str]:
        """Get all available SEHKSTAR symbols."""
        return list(self.symbol_map.keys())
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid SEHKSTAR symbol."""
        return str(symbol).strip() in self.symbol_map
    
    def get_contract_details(self, sehkstar_symbol: str) -> Optional[Dict]:
        """Get contract details for IB API."""
        info = self.get_symbol_info(sehkstar_symbol)
        if not info:
            return None
        
        return {
            'symbol': info['ib_symbol'],
            'secType': 'STK',
            'exchange': 'SEHKSTAR',
            'currency': info['currency'],
            'localSymbol': sehkstar_symbol
        }

# Global instance
sehkstar_mapper = SEHKSTARIBMapper()

def map_sehkstar_to_ib(sehkstar_symbol: str) -> Optional[str]:
    """Convenience function to map SEHKSTAR symbol to IB symbol."""
    return sehkstar_mapper.get_ib_symbol(sehkstar_symbol)

def get_sehkstar_contract(sehkstar_symbol: str) -> Optional[Dict]:
    """Get IB contract details for SEHKSTAR symbol."""
    return sehkstar_mapper.get_contract_details(sehkstar_symbol)

def search_sehkstar_stocks(query: str, limit: int = 10) -> List[Dict]:
    """Search SEHKSTAR stocks."""
    return sehkstar_mapper.search_symbols(query, limit)

if __name__ == "__main__":
    # Test the mapper
    print("SEHKSTAR-IB Mapper Test")
    print("=" * 50)
    
    # Test some Shanghai Stock Exchange stocks
    test_symbols = ['688001', '688002', '688009', '688018', '688036', '688047']
    
    print("\nTesting symbol mappings:")
    for symbol in test_symbols:
        ib_symbol = sehkstar_mapper.get_ib_symbol(symbol)
        info = sehkstar_mapper.get_symbol_info(symbol)
        if info:
            print(f"SEHKSTAR {symbol} -> IB {ib_symbol} ({info['description'][:50]}...)")
        else:
            print(f"SEHKSTAR {symbol} -> Not found")
    
    print(f"\nTotal symbols loaded: {len(sehkstar_mapper.get_all_symbols())}")
    
    # Test search
    print("\nSearch results for 'TECHNOLOGY':")
    results = sehkstar_mapper.search_symbols('TECHNOLOGY', 3)
    for result in results:
        print(f"  {result['sehkstar_symbol']}: {result['description']}")
    
    print("\nSearch results for 'SHANGHAI':")
    results = sehkstar_mapper.search_symbols('SHANGHAI', 3)
    for result in results:
        print(f"  {result['sehkstar_symbol']}: {result['description']}")
