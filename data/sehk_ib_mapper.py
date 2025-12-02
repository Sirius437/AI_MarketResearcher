#!/usr/bin/env python3
"""
SEHK (Hong Kong Stock Exchange) to Interactive Brokers Symbol Mapper

This module provides mapping functionality between SEHK stock symbols and their
corresponding Interactive Brokers symbols for trading and data retrieval.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class SEHKIBMapper:
    """Maps SEHK symbols to Interactive Brokers symbols."""
    
    def __init__(self):
        self.mapping_file = Path(__file__).parent / "exchanges" / "sehk_ib_map.csv"
        self.symbol_map = {}
        self.reverse_map = {}
        self.load_mappings()
    
    def load_mappings(self):
        """Load SEHK to IB symbol mappings from CSV file."""
        try:
            if not self.mapping_file.exists():
                logger.error(f"SEHK mapping file not found: {self.mapping_file}")
                return
            
            df = pd.read_csv(self.mapping_file, sep='\t', on_bad_lines='skip')
            logger.info(f"Loaded {len(df)} SEHK-IB mappings")
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Create symbol mappings
            for _, row in df.iterrows():
                sehk_symbol = str(row['SYMBOL']).strip()
                ib_symbol = str(row['IBKR SYMBOL']).strip()
                description = str(row.get('DESCRIPTION', '')).strip()
                currency = str(row.get('CURRENCY', 'HKD')).strip()
                
                # Skip invalid entries
                if not sehk_symbol or sehk_symbol == 'nan' or not ib_symbol or ib_symbol == 'nan':
                    continue
                
                # Primary mapping: SEHK symbol -> IB symbol
                if sehk_symbol not in self.symbol_map:
                    self.symbol_map[sehk_symbol] = {
                        'ib_symbol': ib_symbol,
                        'description': description,
                        'currency': currency,
                        'exchange': 'SEHK'
                    }
                
                # Reverse mapping for lookups
                self.reverse_map[ib_symbol] = sehk_symbol
            
            logger.info(f"Successfully loaded {len(self.symbol_map)} unique SEHK symbols")
            
        except Exception as e:
            logger.error(f"Error loading SEHK mappings: {e}")
    
    def get_ib_symbol(self, sehk_symbol: str) -> Optional[str]:
        """Get Interactive Brokers symbol for a SEHK symbol."""
        sehk_symbol = str(sehk_symbol).strip()
        mapping = self.symbol_map.get(sehk_symbol)
        return mapping['ib_symbol'] if mapping else None
    
    def get_sehk_symbol(self, ib_symbol: str) -> Optional[str]:
        """Get SEHK symbol from Interactive Brokers symbol."""
        return self.reverse_map.get(str(ib_symbol).strip())
    
    def get_symbol_info(self, sehk_symbol: str) -> Optional[Dict]:
        """Get complete symbol information."""
        return self.symbol_map.get(str(sehk_symbol).strip())
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for symbols by name or symbol."""
        query = query.lower().strip()
        results = []
        
        for symbol, info in self.symbol_map.items():
            if (query in symbol.lower() or 
                query in info.get('description', '').lower()):
                results.append({
                    'sehk_symbol': symbol,
                    'ib_symbol': info['ib_symbol'],
                    'description': info['description'],
                    'currency': info['currency']
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_symbols(self) -> List[str]:
        """Get all available SEHK symbols."""
        return list(self.symbol_map.keys())
    
    def is_valid_symbol(self, symbol: str) -> bool:
        """Check if a symbol is valid SEHK symbol."""
        return str(symbol).strip() in self.symbol_map
    
    def get_contract_details(self, sehk_symbol: str) -> Optional[Dict]:
        """Get contract details for IB API."""
        info = self.get_symbol_info(sehk_symbol)
        if not info:
            return None
        
        return {
            'symbol': info['ib_symbol'],
            'secType': 'STK',
            'exchange': 'SEHK',
            'currency': info['currency'],
            'localSymbol': sehk_symbol
        }

# Global instance
sehk_mapper = SEHKIBMapper()

def map_sehk_to_ib(sehk_symbol: str) -> Optional[str]:
    """Convenience function to map SEHK symbol to IB symbol."""
    return sehk_mapper.get_ib_symbol(sehk_symbol)

def get_sehk_contract(sehk_symbol: str) -> Optional[Dict]:
    """Get IB contract details for SEHK symbol."""
    return sehk_mapper.get_contract_details(sehk_symbol)

def search_sehk_stocks(query: str, limit: int = 10) -> List[Dict]:
    """Search SEHK stocks."""
    return sehk_mapper.search_symbols(query, limit)

if __name__ == "__main__":
    # Test the mapper
    print("SEHK-IB Mapper Test")
    print("=" * 50)
    
    # Test some popular Hong Kong stocks
    test_symbols = ['1', '5', '700', '1024', '1044', '2318', '3988']
    
    print("\nTesting symbol mappings:")
    for symbol in test_symbols:
        ib_symbol = sehk_mapper.get_ib_symbol(symbol)
        info = sehk_mapper.get_symbol_info(symbol)
        if info:
            print(f"SEHK {symbol} -> IB {ib_symbol} ({info['description'][:50]}...)")
        else:
            print(f"SEHK {symbol} -> Not found")
    
    print(f"\nTotal symbols loaded: {len(sehk_mapper.get_all_symbols())}")
    
    # Test search
    print("\nSearch results for 'TENCENT':")
    results = sehk_mapper.search_symbols('TENCENT', 3)
    for result in results:
        print(f"  {result['sehk_symbol']}: {result['description']}")
