from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class CacheConfig(BaseModel):
    strategy: str  # LRU, LFU, ARC, etc.
    max_size: int
    default_ttl: int
    prefetch_threshold: float
    compression_enabled: bool
    encryption_enabled: bool

class CacheEntry(BaseModel):
    key: str
    data: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    size_bytes: int
    metadata: Dict[str, Any]

class CacheMetrics(BaseModel):
    hits: int
    misses: int
    hit_ratio: float
    evictions: int
    memory_usage: float
    avg_lookup_time: float
    prefetch_accuracy: float

class CacheStats(BaseModel):
    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    expirations: int = 0
    last_reset: datetime = datetime.utcnow() 