from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class PerformanceMetrics(BaseModel):
    endpoint_path: str
    avg_response_time: float
    memory_usage: float
    cpu_usage: float
    database_queries: int
    cache_hit_ratio: float
    error_rate: float
    collected_at: datetime

class OptimizationResult(BaseModel):
    endpoint_path: str
    optimizations_applied: List[Dict[str, Any]]
    performance_improvement: float
    metrics_before: PerformanceMetrics
    metrics_after: PerformanceMetrics
    timestamp: datetime 