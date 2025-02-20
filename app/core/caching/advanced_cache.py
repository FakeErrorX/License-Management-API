from typing import Dict, Any, Optional
import asyncio
from datetime import datetime
from app.core.logger import logger
from app.models.caching import CacheConfig, CacheStats

class AdvancedCacheManager:
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache: Dict[str, Any] = {}
        self.stats: CacheStats = CacheStats()
        self.locks: Dict[str, asyncio.Lock] = {}
        
    async def get_cached_data(self, key: str) -> Optional[Any]:
        try:
            if key not in self.cache:
                self.stats.misses += 1
                return None
                
            cache_entry = self.cache[key]
            if self._is_entry_expired(cache_entry):
                del self.cache[key]
                self.stats.expirations += 1
                return None
                
            self.stats.hits += 1
            return cache_entry['data']
        except Exception as e:
            logger.error(f"Cache retrieval failed: {str(e)}")
            return None
            
    async def set_cached_data(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        try:
            if key not in self.locks:
                self.locks[key] = asyncio.Lock()
                
            async with self.locks[key]:
                self.cache[key] = {
                    'data': data,
                    'timestamp': datetime.utcnow(),
                    'ttl': ttl or self.config.default_ttl
                }
                self.stats.sets += 1
                return True
        except Exception as e:
            logger.error(f"Cache set failed: {str(e)}")
            return False 