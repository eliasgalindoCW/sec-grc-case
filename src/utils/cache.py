"""
Cache Module

This module provides caching functionality for API results and analysis data.
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
import logging

from src.utils.config import load_config
from src.utils.logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

class Cache:
    """
    Cache implementation for storing API results and analysis data.
    Uses file-based storage with TTL support.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, ttl_hours: int = 24):
        """
        Initialize cache.
        
        Args:
            cache_dir: Optional cache directory path
            ttl_hours: Cache TTL in hours (default: 24)
        """
        config = load_config()
        self.cache_dir = Path(cache_dir or config.output_dir / "cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        
        logger.info(f"Initialized cache in {self.cache_dir}")
        
    def _get_cache_key(self, key: str) -> str:
        """Generate a safe cache key from input."""
        return hashlib.sha256(key.encode()).hexdigest()
        
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        return self.cache_dir / f"{self._get_cache_key(key)}.json"
        
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        cache_path = self._get_cache_path(key)
        
        try:
            if not cache_path.exists():
                return None
                
            with open(cache_path) as f:
                cached = json.load(f)
                
            # Check TTL
            cached_time = datetime.fromisoformat(cached['timestamp'])
            if datetime.utcnow() - cached_time > self.ttl:
                logger.debug(f"Cache expired for key: {key}")
                return None
                
            logger.debug(f"Cache hit for key: {key}")
            return cached['data']
            
        except Exception as e:
            logger.warning(f"Error reading cache for key {key}: {str(e)}")
            return None
            
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        cache_path = self._get_cache_path(key)
        
        try:
            cached = {
                'timestamp': datetime.utcnow().isoformat(),
                'data': value
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cached, f, indent=2)
                
            logger.debug(f"Cached value for key: {key}")
            
        except Exception as e:
            logger.warning(f"Error writing cache for key {key}: {str(e)}")
            
    def invalidate(self, key: str) -> None:
        """
        Invalidate cached value.
        
        Args:
            key: Cache key to invalidate
        """
        cache_path = self._get_cache_path(key)
        
        try:
            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"Invalidated cache for key: {key}")
                
        except Exception as e:
            logger.warning(f"Error invalidating cache for key {key}: {str(e)}")
            
    def clear(self) -> None:
        """Clear all cached values."""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cleared all cache entries")
            
        except Exception as e:
            logger.warning(f"Error clearing cache: {str(e)}") 