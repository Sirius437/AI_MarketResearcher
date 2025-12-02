"""
SGX to Interactive Brokers symbol mapping functionality.
"""

import os
from typing import Dict, List, Optional

class SGXIBMapper:
    """Maps SGX symbols to Interactive Brokers symbols using the mapping CSV file."""
    
    def __init__(self, csv_path: str = None):
        """Initialize the mapper with the CSV file path."""
        if csv_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, 'sgx_ib_map.csv')
        
        self.csv_path = csv_path
        self._symbol_map: Dict[str, str] = {}
        self._all_mappings: Dict[str, List[str]] = {}  # Store all available mappings for fallback
        self._reverse_map: Dict[str, str] = {}
        self._load_mapping()
    
    def _load_mapping(self):
        """Load the symbol mapping from CSV file."""
        try:
            # First pass: collect all mappings for each SGX symbol
            temp_mappings = {}
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                # Read the file as tab-delimited data
                for line in file:
                    if line.strip():
                        fields = [f.strip() for f in line.split('\t')]
                        if len(fields) >= 6:  # Ensure we have enough fields
                            sgx_symbol = fields[0]
                            company_name = fields[1]
                            ib_symbol = fields[2]
                            
                            if sgx_symbol and ib_symbol:
                                # Store all mappings for each SGX symbol
                                if sgx_symbol not in temp_mappings:
                                    temp_mappings[sgx_symbol] = []
                                temp_mappings[sgx_symbol].append(ib_symbol)
            
            # Second pass: prioritize exact symbol matches, then symbols without .SI suffix
            for sgx_symbol, ib_symbols in temp_mappings.items():
                # Store all available mappings for fallback
                self._all_mappings[sgx_symbol] = ib_symbols
                
                # First priority: exact symbol match
                if sgx_symbol in ib_symbols:
                    self._symbol_map[sgx_symbol] = sgx_symbol
                else:
                    # Second priority: symbols without .SI suffix
                    plain_symbols = [s for s in ib_symbols if not s.endswith('.SI')]
                    if plain_symbols:
                        # Use the first plain symbol
                        self._symbol_map[sgx_symbol] = plain_symbols[0]
                    else:
                        # If no plain symbols, use the first available
                        self._symbol_map[sgx_symbol] = ib_symbols[0]
                
                # Create reverse mappings for all symbols
                for ib_symbol in ib_symbols:
                    self._reverse_map[ib_symbol] = sgx_symbol
                                
        except FileNotFoundError:
            print(f"Warning: SGX-IB mapping file not found at {self.csv_path}")
        except Exception as e:
            print(f"Error loading SGX-IB mapping: {e}")
    
    def sgx_to_ib(self, sgx_symbol: str) -> Optional[str]:
        """Convert SGX symbol to Interactive Brokers symbol."""
        return self._symbol_map.get(sgx_symbol)
    
    def ib_to_sgx(self, ib_symbol: str) -> Optional[str]:
        """Convert Interactive Brokers symbol to SGX symbol."""
        return self._reverse_map.get(ib_symbol)
    
    def get_ib_symbol_for_data(self, sgx_symbol: str) -> str:
        """
        Get the appropriate symbol for data retrieval from Interactive Brokers.
        Based on test results, direct symbols (e.g., D05, O39) work better than
        IB-specific symbols (e.g., YDBSU25_A1, YOCBU25).
        """
        # Remove .SI suffix if present for IB queries
        clean_symbol = sgx_symbol.replace('.SI', '') if sgx_symbol.endswith('.SI') else sgx_symbol
        
        # Based on test results, direct symbols work best with IB
        # Return the plain symbol without any prefixes
        return clean_symbol
            
    def get_all_symbol_alternatives(self, sgx_symbol: str) -> list:
        """
        Get all alternative IB symbols for an SGX symbol.
        Useful for fallback mechanisms when the primary symbol fails.
        """
        return self._all_mappings.get(sgx_symbol, [])
    
    def is_mapped(self, sgx_symbol: str) -> bool:
        """Check if an SGX symbol has an IB mapping."""
        return sgx_symbol in self._symbol_map
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all SGX to IB symbol mappings."""
        return self._symbol_map.copy()
    
    def get_mapping_count(self) -> int:
        """Get the number of symbol mappings loaded."""
        return len(self._symbol_map)

# Global instance for easy access
_mapper_instance = None

def get_sgx_ib_mapper() -> SGXIBMapper:
    """Get the global SGX-IB mapper instance."""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = SGXIBMapper()
    return _mapper_instance

def sgx_to_ib_symbol(sgx_symbol: str) -> Optional[str]:
    """Convenience function to convert SGX symbol to IB symbol."""
    return get_sgx_ib_mapper().sgx_to_ib(sgx_symbol)

def get_ib_symbol_for_data(sgx_symbol: str) -> str:
    """Convenience function to get IB symbol for data retrieval."""
    return get_sgx_ib_mapper().get_ib_symbol_for_data(sgx_symbol)
