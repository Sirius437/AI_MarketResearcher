#!/usr/bin/env python3
"""
BSE (Bombay Stock Exchange) to Interactive Brokers Symbol Mapper

This module provides mapping functionality between BSE stock symbols
and their corresponding Interactive Brokers symbols for trading.
"""

import csv
import os
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class BSEStockInfo:
    """Information about a BSE stock."""
    symbol: str
    description: str
    ib_symbol: str
    currency: str
    region: str
    exchange: str

class BSEIBMapper:
    """Maps BSE symbols to Interactive Brokers symbols."""
    
    def __init__(self):
        """Initialize the mapper with BSE to IB symbol mappings."""
        self.symbol_map: Dict[str, BSEStockInfo] = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load BSE to IB symbol mappings from CSV file."""
        csv_path = os.path.join(os.path.dirname(__file__), 'exchanges', 'india_ib_map.csv')
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file, delimiter='\t')
                
                for row in reader:
                    # Handle column names with trailing spaces
                    symbol_key = 'SYMBOL ' if 'SYMBOL ' in row else 'SYMBOL'
                    desc_key = 'DESCRIPTION ' if 'DESCRIPTION ' in row else 'DESCRIPTION'
                    ib_key = 'IBKR SYMBOL ' if 'IBKR SYMBOL ' in row else 'IBKR SYMBOL'
                    currency_key = 'CURRENCY ' if 'CURRENCY ' in row else 'CURRENCY'
                    region_key = 'REGION ' if 'REGION ' in row else 'REGION'
                    exchange_key = 'EXCHANGE ' if 'EXCHANGE ' in row else 'EXCHANGE'
                    
                    # Skip header row and empty rows
                    if not row.get(symbol_key) or row[symbol_key].strip() == 'SYMBOL':
                        continue
                    
                    bse_symbol = row[symbol_key].strip()
                    description = row.get(desc_key, '').strip()
                    ib_symbol = row.get(ib_key, '').strip()
                    currency = row.get(currency_key, 'INR').strip()
                    region = row.get(region_key, 'IN').strip()
                    exchange = row.get(exchange_key, 'NSE').strip()
                    
                    if bse_symbol and ib_symbol:
                        self.symbol_map[bse_symbol] = BSEStockInfo(
                            symbol=bse_symbol,
                            description=description,
                            ib_symbol=ib_symbol,
                            currency=currency,
                            region=region,
                            exchange=exchange
                        )
                        
                        # Also map with .BO suffix for BSE
                        bse_symbol_bo = f"{bse_symbol}.BO"
                        self.symbol_map[bse_symbol_bo] = BSEStockInfo(
                            symbol=bse_symbol_bo,
                            description=description,
                            ib_symbol=ib_symbol,
                            currency=currency,
                            region=region,
                            exchange="BSE"
                        )
                        
        except FileNotFoundError:
            print(f"Warning: BSE mapping file not found at {csv_path}")
        except Exception as e:
            print(f"Error loading BSE mappings: {e}")
            import traceback
            traceback.print_exc()
    
    def get_ib_symbol(self, bse_symbol: str) -> Optional[str]:
        """
        Get Interactive Brokers symbol for a BSE symbol.
        
        Args:
            bse_symbol: BSE stock symbol (e.g., 'RELIANCE' or 'RELIANCE.BO')
            
        Returns:
            IB symbol if found, None otherwise
        """
        # Try exact match first
        stock_info = self.symbol_map.get(bse_symbol)
        if stock_info:
            return stock_info.ib_symbol
        
        # Try without .BO suffix
        if bse_symbol.endswith('.BO'):
            base_symbol = bse_symbol[:-3]
            stock_info = self.symbol_map.get(base_symbol)
            if stock_info:
                return stock_info.ib_symbol
        
        # Try with .BO suffix
        else:
            bo_symbol = f"{bse_symbol}.BO"
            stock_info = self.symbol_map.get(bo_symbol)
            if stock_info:
                return stock_info.ib_symbol
        
        return None
    
    def get_currency(self, bse_symbol: str) -> str:
        """
        Get currency for a BSE symbol.
        
        Args:
            bse_symbol: BSE stock symbol
            
        Returns:
            Currency code (default: INR)
        """
        stock_info = self.symbol_map.get(bse_symbol)
        if stock_info:
            return stock_info.currency
        
        # Try alternative formats
        if bse_symbol.endswith('.BO'):
            base_symbol = bse_symbol[:-3]
            stock_info = self.symbol_map.get(base_symbol)
            if stock_info:
                return stock_info.currency
        else:
            bo_symbol = f"{bse_symbol}.BO"
            stock_info = self.symbol_map.get(bo_symbol)
            if stock_info:
                return stock_info.currency
        
        return "INR"  # Default currency for Indian stocks
    
    def get_stock_info(self, bse_symbol: str) -> Optional[BSEStockInfo]:
        """
        Get complete stock information for a BSE symbol.
        
        Args:
            bse_symbol: BSE stock symbol
            
        Returns:
            BSEStockInfo object if found, None otherwise
        """
        # Try exact match first
        stock_info = self.symbol_map.get(bse_symbol)
        if stock_info:
            return stock_info
        
        # Try alternative formats
        if bse_symbol.endswith('.BO'):
            base_symbol = bse_symbol[:-3]
            return self.symbol_map.get(base_symbol)
        else:
            bo_symbol = f"{bse_symbol}.BO"
            return self.symbol_map.get(bo_symbol)
        
        return None
    
    def search_symbols(self, query: str, limit: int = 10) -> List[BSEStockInfo]:
        """
        Search for symbols matching the query.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching BSEStockInfo objects
        """
        query_lower = query.lower()
        results = []
        
        for stock_info in self.symbol_map.values():
            if (query_lower in stock_info.symbol.lower() or 
                query_lower in stock_info.description.lower()):
                results.append(stock_info)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_all_symbols(self) -> List[str]:
        """Get all available BSE symbols."""
        return list(self.symbol_map.keys())
    
    def get_symbol_count(self) -> int:
        """Get total number of mapped symbols."""
        return len(self.symbol_map)

# Create global instance
bse_ib_mapper = BSEIBMapper()

def get_ib_symbol(bse_symbol: str) -> Optional[str]:
    """Convenience function to get IB symbol."""
    return bse_ib_mapper.get_ib_symbol(bse_symbol)

def get_currency(bse_symbol: str) -> str:
    """Convenience function to get currency."""
    return bse_ib_mapper.get_currency(bse_symbol)

def get_stock_info(bse_symbol: str) -> Optional[BSEStockInfo]:
    """Convenience function to get stock info."""
    return bse_ib_mapper.get_stock_info(bse_symbol)

if __name__ == "__main__":
    # Test the mapper
    mapper = BSEIBMapper()
    
    print("🇮🇳 BSE to Interactive Brokers Symbol Mapper Test")
    print("=" * 60)
    
    # Test some popular Indian stocks
    test_symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK', 'ICICIBANK', 'SBIN', 'ITC', 'HINDUNILVR']
    
    print(f"Total symbols loaded: {mapper.get_symbol_count()}")
    print()
    
    for symbol in test_symbols:
        ib_symbol = mapper.get_ib_symbol(symbol)
        currency = mapper.get_currency(symbol)
        stock_info = mapper.get_stock_info(symbol)
        
        if ib_symbol:
            print(f"✅ {symbol} -> {ib_symbol} ({currency})")
            if stock_info:
                print(f"   Description: {stock_info.description}")
        else:
            print(f"❌ {symbol} -> No mapping found")
        print()
