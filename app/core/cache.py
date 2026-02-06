"""Redis cache manager for high-performance caching."""

import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
from redis import Redis
from app.config import settings

# Redis client instance
redis_client = Redis.from_url(
    settings.redis_url,
    max_connections=settings.redis_max_connections,
    decode_responses=True
)


class CacheManager:
    """Manage Redis caching operations."""
    
    def __init__(self):
        self.client = redis_client
        self.default_ttl = settings.cache_ttl_seconds
        self.enabled = settings.cache_enabled
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate cache key from prefix and parameters.
        
        Args:
            prefix: Key prefix
            **kwargs: Parameters to include in key
            
        Returns:
            Generated cache key
        """
        # Sort kwargs for consistent key generation
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{params_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            return bool(self.client.setex(key, ttl, serialized))
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Key pattern (e.g., "products:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return 0
    
    def invalidate_products(self):
        """Invalidate all product-related caches."""
        return self.delete_pattern("products:*")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        try:
            info = self.client.info("stats")
            return {
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {"hits": 0, "misses": 0, "hit_rate": 0.0}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


def cache_result(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = CacheManager()
            
            # Generate cache key from function arguments
            cache_key = cache._generate_key(prefix, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# Global cache manager instance
cache_manager = CacheManager()
