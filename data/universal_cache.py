"""Universal caching system for all market data APIs."""

import asyncio
import logging
import json
import pickle
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
import pandas as pd

from config.settings import MarketResearcherConfig

logger = logging.getLogger(__name__)


class UniversalCache:
    """Universal caching system for all market data types."""
    
    def __init__(self, config: MarketResearcherConfig):
        """Initialize universal cache."""
        self.config = config
        self.cache_dir = Path(config.data_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache expiry times for different data types (in seconds)
        self.cache_expiry = {
            'crypto': 300,      # 5 minutes
            'stocks': 300,      # 5 minutes
            'forex': 300,       # 5 minutes
            'bonds': 600,       # 10 minutes
            'commodities': 600, # 10 minutes
            'derivatives': 300, # 5 minutes
            'options': 180,     # 3 minutes
            'futures': 300,     # 5 minutes
            'news': 1800,       # 30 minutes
            'economic_data': 3600, # 1 hour
            'yield_curve': 1800,   # 30 minutes
            'volatility': 180      # 3 minutes
        }
        
        # In-memory cache for frequently accessed data
        self._memory_cache = {}
        self._cache_timestamps = {}
    
    def _generate_cache_key(self, data_type: str, identifier: str, **kwargs) -> str:
        """Generate a unique cache key."""
        # Create a hash of the parameters for consistent key generation
        params_str = json.dumps(kwargs, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        return f"{data_type}_{identifier}_{params_hash}"
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def _is_cache_valid(self, cache_key: str, data_type: str) -> bool:
        """Check if cached data is still valid."""
        # Check memory cache first
        if cache_key in self._cache_timestamps:
            time_diff = datetime.now() - self._cache_timestamps[cache_key]
            expiry_time = self.cache_expiry.get(data_type, 300)
            return time_diff.total_seconds() < expiry_time
        
        # Check file cache
        cache_file = self._get_cache_file_path(cache_key)
        if cache_file.exists():
            try:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                time_diff = datetime.now() - file_time
                expiry_time = self.cache_expiry.get(data_type, 300)
                return time_diff.total_seconds() < expiry_time
            except Exception as e:
                logger.error(f"Error checking cache file timestamp: {e}")
                return False
        
        return False
    
    def get(self, data_type: str, identifier: str, **kwargs) -> Optional[Any]:
        """Get data from cache."""
        try:
            cache_key = self._generate_cache_key(data_type, identifier, **kwargs)
            
            if not self._is_cache_valid(cache_key, data_type):
                return None
            
            # Try memory cache first
            if cache_key in self._memory_cache:
                logger.debug(f"Cache hit (memory): {cache_key}")
                return self._memory_cache[cache_key]
            
            # Try file cache
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        data = pickle.load(f)
                    
                    # Store in memory cache for faster access
                    self._memory_cache[cache_key] = data
                    self._cache_timestamps[cache_key] = datetime.now()
                    
                    logger.debug(f"Cache hit (file): {cache_key}")
                    return data
                except Exception as e:
                    logger.error(f"Error reading cache file {cache_file}: {e}")
                    # Remove corrupted cache file
                    cache_file.unlink(missing_ok=True)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached data: {e}")
            return None
    
    def set(self, data_type: str, identifier: str, data: Any, **kwargs) -> bool:
        """Store data in cache."""
        try:
            cache_key = self._generate_cache_key(data_type, identifier, **kwargs)
            
            # Store in memory cache
            self._memory_cache[cache_key] = data
            self._cache_timestamps[cache_key] = datetime.now()
            
            # Store in file cache
            cache_file = self._get_cache_file_path(cache_key)
            # Ensure parent directory exists
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            
            logger.debug(f"Data cached: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching data: {e}")
            return False
    
    def invalidate(self, data_type: str, identifier: str = None, **kwargs) -> bool:
        """Invalidate cached data."""
        try:
            if identifier:
                # Invalidate specific cache entry
                cache_key = self._generate_cache_key(data_type, identifier, **kwargs)
                
                # Remove from memory cache
                self._memory_cache.pop(cache_key, None)
                self._cache_timestamps.pop(cache_key, None)
                
                # Remove from file cache
                cache_file = self._get_cache_file_path(cache_key)
                cache_file.unlink(missing_ok=True)
                
                logger.debug(f"Cache invalidated: {cache_key}")
            else:
                # Invalidate all cache entries for data type
                pattern = f"{data_type}_*"
                for cache_file in self.cache_dir.glob(f"{pattern}.pkl"):
                    cache_file.unlink(missing_ok=True)
                
                # Remove from memory cache
                keys_to_remove = [k for k in self._memory_cache.keys() if k.startswith(f"{data_type}_")]
                for key in keys_to_remove:
                    self._memory_cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)
                
                logger.debug(f"All cache invalidated for data type: {data_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Clear all cached data."""
        try:
            # Clear memory cache
            self._memory_cache.clear()
            self._cache_timestamps.clear()
            
            # Clear file cache
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink(missing_ok=True)
            
            logger.info("All cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            memory_count = len(self._memory_cache)
            file_count = len(list(self.cache_dir.glob("*.pkl")))
            
            # Calculate cache size
            total_size = 0
            for cache_file in self.cache_dir.glob("*.pkl"):
                total_size += cache_file.stat().st_size
            
            # Group by data type
            data_types = {}
            for cache_file in self.cache_dir.glob("*.pkl"):
                data_type = cache_file.stem.split('_')[0]
                if data_type not in data_types:
                    data_types[data_type] = 0
                data_types[data_type] += 1
            
            return {
                'memory_cache_entries': memory_count,
                'file_cache_entries': file_count,
                'total_cache_size_bytes': total_size,
                'total_cache_size_mb': round(total_size / (1024 * 1024), 2),
                'data_types': data_types,
                'cache_directory': str(self.cache_dir),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries."""
        try:
            cleaned_count = 0
            
            for cache_file in self.cache_dir.glob("*.pkl"):
                try:
                    # Extract data type from filename
                    data_type = cache_file.stem.split('_')[0]
                    
                    # Check if expired
                    file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                    time_diff = datetime.now() - file_time
                    expiry_time = self.cache_expiry.get(data_type, 300)
                    
                    if time_diff.total_seconds() > expiry_time:
                        cache_file.unlink()
                        cleaned_count += 1
                        
                        # Also remove from memory cache
                        cache_key = cache_file.stem
                        self._memory_cache.pop(cache_key, None)
                        self._cache_timestamps.pop(cache_key, None)
                        
                except Exception as e:
                    logger.error(f"Error processing cache file {cache_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired cache entries")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")
            return 0
    
    def get_or_fetch(self, data_type: str, identifier: str, fetch_func, **kwargs) -> Any:
        """Get data from cache or fetch if not available."""
        try:
            # Try to get from cache first
            cached_data = self.get(data_type, identifier, **kwargs)
            if cached_data is not None:
                return cached_data
            
            # Fetch fresh data
            fresh_data = fetch_func(**kwargs)
            
            # Cache the fresh data
            if fresh_data is not None:
                self.set(data_type, identifier, fresh_data, **kwargs)
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"Error in get_or_fetch for {data_type}:{identifier}: {e}")
            return None
    
    async def get_or_fetch_async(self, data_type: str, identifier: str, fetch_func, **kwargs) -> Any:
        """Async version of get_or_fetch."""
        try:
            # Try to get from cache first
            cached_data = self.get(data_type, identifier, **kwargs)
            if cached_data is not None:
                return cached_data
            
            # Fetch fresh data asynchronously
            fresh_data = await fetch_func(**kwargs)
            
            # Cache the fresh data
            if fresh_data is not None:
                self.set(data_type, identifier, fresh_data, **kwargs)
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"Error in async get_or_fetch for {data_type}:{identifier}: {e}")
            return None
