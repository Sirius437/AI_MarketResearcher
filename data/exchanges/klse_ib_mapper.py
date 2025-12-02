"""
KLSE to Interactive Brokers symbol mapping functionality.
"""

import csv
import os
from typing import Dict, Optional
from .klse_numeric_to_symbol_map import get_symbol_from_numeric_code, is_numeric_klse_code

class KLSEIBMapper:
    """Maps KLSE symbols to Interactive Brokers symbols using the mapping CSV file."""
    
    def __init__(self, csv_path: str = None):
        """Initialize the mapper with the CSV file path."""
        if csv_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, 'klse_ib_map.csv')
        
        self.csv_path = csv_path
        self._symbol_map: Dict[str, str] = {}
        self._reverse_map: Dict[str, str] = {}
        self._load_mapping()
    
    def _load_mapping(self):
        """Load the symbol mapping from CSV file."""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                # Read the first line as comma-delimited header
                header_line = file.readline().strip()
                headers = [h.strip() for h in header_line.split(',')]
                
                # Find the column indices
                symbol_idx = headers.index('SYMBOL')
                ibkr_symbol_idx = headers.index('IBKR SYMBOL')
                
                # Read the rest as tab-delimited data
                for line in file:
                    if line.strip():
                        fields = [f.strip() for f in line.split('\t')]
                        if len(fields) > max(symbol_idx, ibkr_symbol_idx):
                            klse_symbol = fields[symbol_idx]
                            ib_symbol = fields[ibkr_symbol_idx]
                            
                            if klse_symbol and ib_symbol:
                                self._symbol_map[klse_symbol] = ib_symbol
                                self._reverse_map[ib_symbol] = klse_symbol
                                
        except FileNotFoundError:
            print(f"Warning: KLSE-IB mapping file not found at {self.csv_path}")
        except Exception as e:
            print(f"Error loading KLSE-IB mapping: {e}")
    
    def klse_to_ib(self, klse_symbol: str) -> Optional[str]:
        """Convert KLSE symbol to Interactive Brokers symbol."""
        return self._symbol_map.get(klse_symbol)
    
    def ib_to_klse(self, ib_symbol: str) -> Optional[str]:
        """Convert Interactive Brokers symbol to KLSE symbol."""
        return self._reverse_map.get(ib_symbol)
    
    def get_ib_symbol_for_data(self, klse_symbol: str) -> str:
        """
        Get the appropriate symbol for data retrieval from Interactive Brokers.
        Returns IB symbol if mapping exists, otherwise returns original symbol.
        Handles both numeric KLSE codes and text symbols.
        """
        # Convert numeric KLSE codes to text symbols first
        if is_numeric_klse_code(klse_symbol):
            text_symbol = get_symbol_from_numeric_code(klse_symbol)
            ib_symbol = self.klse_to_ib(text_symbol)
            return ib_symbol if ib_symbol else text_symbol
        else:
            ib_symbol = self.klse_to_ib(klse_symbol)
            return ib_symbol if ib_symbol else klse_symbol
    
    def is_mapped(self, klse_symbol: str) -> bool:
        """Check if a KLSE symbol has an IB mapping."""
        return klse_symbol in self._symbol_map
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all KLSE to IB symbol mappings."""
        return self._symbol_map.copy()
    
    def get_mapping_count(self) -> int:
        """Get the number of symbol mappings loaded."""
        return len(self._symbol_map)

# Global instance for easy access
_mapper_instance = None

def get_klse_ib_mapper() -> KLSEIBMapper:
    """Get the global KLSE-IB mapper instance."""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = KLSEIBMapper()
    return _mapper_instance

def klse_to_ib_symbol(klse_symbol: str) -> Optional[str]:
    """Convenience function to convert KLSE symbol to IB symbol."""
    return get_klse_ib_mapper().klse_to_ib(klse_symbol)

def get_ib_symbol_for_data(klse_symbol: str) -> str:
    """Convenience function to get IB symbol for data retrieval."""
    return get_klse_ib_mapper().get_ib_symbol_for_data(klse_symbol)

