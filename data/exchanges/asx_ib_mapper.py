"""
ASX to Interactive Brokers symbol mapping functionality.
"""

import csv
import os
from typing import Dict, Optional

class ASXIBMapper:
    """Maps ASX symbols to Interactive Brokers symbols using the mapping CSV file."""
    
    def __init__(self, csv_path: str = None):
        """Initialize the mapper with the CSV file path."""
        if csv_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(current_dir, 'asx_ib_map.csv')
        
        self.csv_path = csv_path
        self._symbol_map: Dict[str, str] = {}
        self._all_mappings: Dict[str, List[str]] = {}  # Store all available mappings for fallback
        self._reverse_map: Dict[str, str] = {}
        self._load_mapping()
    
    def _load_mapping(self):
        """Load the symbol mapping from CSV file."""
        try:
            # First pass: collect all mappings for each ASX symbol
            temp_mappings = {}
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                # Read the file as tab-delimited data
                for line in file:
                    if line.strip():
                        fields = [f.strip() for f in line.split('\t')]
                        if len(fields) >= 6:  # Ensure we have enough fields
                            asx_symbol = fields[0]
                            company_name = fields[1]
                            ib_symbol = fields[2]
                            
                            if asx_symbol and ib_symbol:
                                # Store all mappings for each ASX symbol
                                if asx_symbol not in temp_mappings:
                                    temp_mappings[asx_symbol] = []
                                temp_mappings[asx_symbol].append(ib_symbol)
            
            # Second pass: prioritize exact symbol matches, then symbols without .E suffix
            for asx_symbol, ib_symbols in temp_mappings.items():
                # Store all available mappings for fallback
                self._all_mappings[asx_symbol] = ib_symbols
                
                # First priority: exact symbol match
                if asx_symbol in ib_symbols:
                    self._symbol_map[asx_symbol] = asx_symbol
                else:
                    # Second priority: symbols without .E suffix
                    plain_symbols = [s for s in ib_symbols if not s.endswith('.E')]
                    if plain_symbols:
                        # Use the first plain symbol
                        self._symbol_map[asx_symbol] = plain_symbols[0]
                    else:
                        # If no plain symbols, use the first available
                        self._symbol_map[asx_symbol] = ib_symbols[0]
                
                # Create reverse mappings for all symbols
                for ib_symbol in ib_symbols:
                    self._reverse_map[ib_symbol] = asx_symbol
                                
        except FileNotFoundError:
            print(f"Warning: ASX-IB mapping file not found at {self.csv_path}")
        except Exception as e:
            print(f"Error loading ASX-IB mapping: {e}")
    
    def asx_to_ib(self, asx_symbol: str) -> Optional[str]:
        """Convert ASX symbol to Interactive Brokers symbol."""
        return self._symbol_map.get(asx_symbol)
    
    def ib_to_asx(self, ib_symbol: str) -> Optional[str]:
        """Convert Interactive Brokers symbol to ASX symbol."""
        return self._reverse_map.get(ib_symbol)
    
    def get_ib_symbol_for_data(self, asx_symbol: str) -> str:
        """
        Get the appropriate symbol for data retrieval from Interactive Brokers.
        Returns IB symbol if mapping exists, otherwise returns original symbol with .AX suffix.
        Includes fallback options for problematic symbols.
        """
        # First try the primary mapping
        ib_symbol = self.asx_to_ib(asx_symbol)
        
        # If we have alternative mappings available, return them as a list
        if asx_symbol in self._all_mappings:
            # Return the primary mapping first, but include all alternatives
            all_symbols = self._all_mappings[asx_symbol]
            
            # If the primary mapping is in the list, prioritize it
            if ib_symbol in all_symbols:
                # Move the primary mapping to the front
                all_symbols = [ib_symbol] + [s for s in all_symbols if s != ib_symbol]
            
            # Return the primary symbol (either from _symbol_map or the first alternative)
            return all_symbols[0]
        elif ib_symbol:
            # If we have a primary mapping but no alternatives, use it
            return ib_symbol
        else:
            # Default IB format for ASX stocks is SYMBOL.AX
            return f"{asx_symbol}.AX"
            
    def get_all_symbol_alternatives(self, asx_symbol: str) -> list:
        """
        Get all alternative IB symbols for an ASX symbol.
        Useful for fallback mechanisms when the primary symbol fails.
        """
        return self._all_mappings.get(asx_symbol, [])
    
    def is_mapped(self, asx_symbol: str) -> bool:
        """Check if an ASX symbol has an IB mapping."""
        return asx_symbol in self._symbol_map
    
    def get_all_mappings(self) -> Dict[str, str]:
        """Get all ASX to IB symbol mappings."""
        return self._symbol_map.copy()
    
    def get_mapping_count(self) -> int:
        """Get the number of symbol mappings loaded."""
        return len(self._symbol_map)

# Global instance for easy access
_mapper_instance = None

def get_asx_ib_mapper() -> ASXIBMapper:
    """Get the global ASX-IB mapper instance."""
    global _mapper_instance
    if _mapper_instance is None:
        _mapper_instance = ASXIBMapper()
    return _mapper_instance

def asx_to_ib_symbol(asx_symbol: str) -> Optional[str]:
    """Convenience function to convert ASX symbol to IB symbol."""
    return get_asx_ib_mapper().asx_to_ib(asx_symbol)

def get_ib_symbol_for_data(asx_symbol: str) -> str:
    """Convenience function to get IB symbol for data retrieval."""
    return get_asx_ib_mapper().get_ib_symbol_for_data(asx_symbol)
    
def get_all_symbol_alternatives(asx_symbol: str) -> list:
    """Get all alternative IB symbols for an ASX symbol."""
    return get_asx_ib_mapper().get_all_symbol_alternatives(asx_symbol)

def get_asx_contract_details(asx_symbol: str) -> dict:
    """
    Get the contract details for an ASX stock.
    Returns a dictionary with symbol, exchange, and currency information.
    """
    return {
        "symbol": get_ib_symbol_for_data(asx_symbol),
        "exchange": "ASX",  # Always use ASX exchange for Australian stocks
        "currency": "AUD",  # Australian Dollar
        "asset_type": "stock",
        "alternatives": get_all_symbol_alternatives(asx_symbol)  # Include all alternatives for fallback
    }
