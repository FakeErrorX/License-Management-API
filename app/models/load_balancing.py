from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class ServerNode(BaseModel):
    id: str
    host: str
    port: int
    location: Dict[str, float]  # lat, long
    capabilities: Dict[str, Any]
    status: str
    last_health_check: datetime

class LoadBalancerConfig(BaseModel):
    algorithm: str
    health_check_interval: int
    failure_threshold: int
    success_threshold: int
    enabled_features: List[str]

class BalancingMetrics(BaseModel):
    node_id: str
    current_load: float
    avg_latency: float
    uptime: float
    error_rate: float
    resource_usage: Dict[str, float]
    collected_at: datetime 