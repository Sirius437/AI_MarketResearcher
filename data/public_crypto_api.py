"""
Public cryptocurrency price API client that doesn't require API keys.
Uses CoinGecko public API for basic price data.
"""

import requests
import logging
import time
import json
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PublicCryptoAPI:
    """Public cryptocurrency API client that doesn't require API keys."""
    
    def __init__(self):
        """Initialize the public crypto API client."""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache_dir = "cache/crypto_public"
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_symbol_mapping(self, symbol: str) -> str:
        """Map exchange symbols to CoinGecko IDs."""
        # Common mappings for popular cryptocurrencies
        mapping = {
            "BTCUSDT": "bitcoin",
            "ETHUSDT": "ethereum",
            "BNBUSDT": "binancecoin",
            "ADAUSDT": "cardano",
            "SOLUSDT": "solana",
            "DOGEUSDT": "dogecoin",
            "DOTUSDT": "polkadot",
            "XRPUSDT": "ripple",
            "LTCUSDT": "litecoin",
            "LINKUSDT": "chainlink",
            "UNIUSDT": "uniswap",
            "AVAXUSDT": "avalanche-2",
            "MATICUSDT": "matic-network",
            "SHIBUSDT": "shiba-inu",
        }
        
        # Try direct mapping first
        if symbol in mapping:
            return mapping[symbol]
        
        # Remove common suffixes and try again
        base_symbol = symbol.replace("USDT", "").replace("USD", "").replace("BTC", "").lower()
        
        # For symbols not in the mapping, make a best guess
        return base_symbol
    
    def get_ticker_data(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Get ticker data for a cryptocurrency symbol."""
        cache_file = f"{self.cache_dir}/{symbol.lower()}_ticker.json"
        cache_duration = 300  # 5 minutes
        
        # Check cache first unless force refresh is requested
        if not force_refresh and os.path.exists(cache_file):
            try:
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < cache_duration:
                    with open(cache_file, 'r') as f:
                        cached_data = json.load(f)
                        logger.info(f"Using cached public API data for {symbol} (age: {cache_age:.1f}s)")
                        return cached_data
            except Exception as e:
                logger.warning(f"Error reading cache for {symbol}: {e}")
        
        # Get coin ID for the symbol
        coin_id = self.get_symbol_mapping(symbol)
        
        try:
            # Fetch data from CoinGecko API
            url = f"{self.base_url}/coins/{coin_id}"
            response = requests.get(url, params={"localization": "false", "tickers": "true", "market_data": "true"})
            
            if response.status_code != 200:
                logger.error(f"Error fetching data for {symbol}: {response.status_code}")
                return {}
            
            data = response.json()
            
            # Extract relevant data
            market_data = data.get("market_data", {})
            current_price = market_data.get("current_price", {}).get("usd", 0)
            price_change_24h = market_data.get("price_change_24h", 0)
            price_change_percentage_24h = market_data.get("price_change_percentage_24h", 0)
            volume = market_data.get("total_volume", {}).get("usd", 0)
            
            result = {
                "symbol": symbol,
                "price": current_price,
                "priceChange": price_change_24h,
                "priceChangePercent": price_change_percentage_24h,
                "volume": volume,
                "timestamp": time.time()
            }
            
            # Cache the result
            try:
                with open(cache_file, 'w') as f:
                    json.dump(result, f)
                logger.info(f"Cached fresh public API data for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to cache data for {symbol}: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching public API data for {symbol}: {e}")
            return {}
    
    def get_market_overview(self, symbol: str) -> Dict[str, Any]:
        """Get market overview data for a cryptocurrency symbol."""
        ticker_data = self.get_ticker_data(symbol)
        if not ticker_data:
            return {}
        
        return {
            "price": ticker_data.get("price", 0),
            "change_24h": ticker_data.get("priceChange", 0),
            "change_percent_24h": ticker_data.get("priceChangePercent", 0),
            "volume": ticker_data.get("volume", 0)
        }
