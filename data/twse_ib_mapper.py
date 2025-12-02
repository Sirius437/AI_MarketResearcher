"""
Taiwan Stock Exchange (TWSE) to Interactive Brokers symbol mapper.
Maps TWSE symbols to their corresponding IB symbols for trading.
"""

import csv
import os
from typing import Dict, Optional, Tuple

class TWSEIBMapper:
    def __init__(self):
        self.twse_to_ib: Dict[str, Tuple[str, str, str]] = {}  # symbol -> (ib_symbol, currency, exchange)
        self.ib_to_twse: Dict[str, str] = {}  # ib_symbol -> twse_symbol
        self._load_mapping()
    
    def _load_mapping(self):
        """Load TWSE to IB symbol mapping from CSV file."""
        csv_path = os.path.join(os.path.dirname(__file__), 'exchanges', 'TWSE_ib_map.csv')
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                # Skip header row
                next(file)
                
                for line in file:
                    # Split by tab (TSV format)
                    parts = line.strip().split('\t')
                    if len(parts) >= 6:
                        twse_symbol = parts[0].strip()
                        description = parts[1].strip()
                        ib_symbol = parts[2].strip()
                        currency = parts[3].strip()
                        region = parts[4].strip()
                        exchange = parts[5].strip()
                        
                        # Skip empty or invalid entries
                        if not twse_symbol or not ib_symbol or twse_symbol == 'SYMBOL':
                            continue
                        
                        # Store mapping
                        self.twse_to_ib[twse_symbol] = (ib_symbol, currency, exchange)
                        self.ib_to_twse[ib_symbol] = twse_symbol
                        
        except FileNotFoundError:
            print(f"Warning: TWSE IB mapping file not found at {csv_path}")
        except Exception as e:
            print(f"Error loading TWSE IB mapping: {e}")
    
    def get_ib_symbol(self, twse_symbol: str) -> Optional[str]:
        """Get IB symbol for a given TWSE symbol."""
        mapping = self.twse_to_ib.get(twse_symbol)
        return mapping[0] if mapping else None
    
    def get_twse_symbol(self, ib_symbol: str) -> Optional[str]:
        """Get TWSE symbol for a given IB symbol."""
        return self.ib_to_twse.get(ib_symbol)
    
    def get_currency(self, twse_symbol: str) -> Optional[str]:
        """Get currency for a given TWSE symbol."""
        mapping = self.twse_to_ib.get(twse_symbol)
        return mapping[1] if mapping else None
    
    def get_exchange(self, twse_symbol: str) -> Optional[str]:
        """Get exchange for a given TWSE symbol."""
        mapping = self.twse_to_ib.get(twse_symbol)
        return mapping[2] if mapping else None
    
    def search_symbol(self, query: str, limit: int = 10) -> list:
        """Search for symbols matching the query."""
        query = query.upper()
        results = []
        
        for twse_symbol, (ib_symbol, currency, exchange) in self.twse_to_ib.items():
            if query in twse_symbol.upper() or query in ib_symbol.upper():
                results.append({
                    'twse_symbol': twse_symbol,
                    'ib_symbol': ib_symbol,
                    'currency': currency,
                    'exchange': exchange
                })
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_contract_details(self, twse_symbol: str) -> Optional[dict]:
        """Get contract details for IB API."""
        mapping = self.twse_to_ib.get(twse_symbol)
        if not mapping:
            return None
        
        ib_symbol, currency, exchange = mapping
        
        return {
            'symbol': ib_symbol,
            'secType': 'STK',
            'exchange': 'TWSE',
            'currency': currency,
            'primaryExchange': 'TWSE'
        }
    
    def get_stats(self) -> dict:
        """Get mapping statistics."""
        return {
            'total_symbols': len(self.twse_to_ib),
            'currencies': list(set(mapping[1] for mapping in self.twse_to_ib.values())),
            'exchanges': list(set(mapping[2] for mapping in self.twse_to_ib.values()))
        }

# Global instance
twse_ib_mapper = TWSEIBMapper()

def get_ib_symbol(twse_symbol: str) -> Optional[str]:
    """Convenience function to get IB symbol."""
    return twse_ib_mapper.get_ib_symbol(twse_symbol)

def get_contract_details(twse_symbol: str) -> Optional[dict]:
    """Convenience function to get contract details."""
    return twse_ib_mapper.get_contract_details(twse_symbol)

def search_symbol(query: str, limit: int = 10) -> list:
    """Convenience function to search symbols."""
    return twse_ib_mapper.search_symbol(query, limit)
