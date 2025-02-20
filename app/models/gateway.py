from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class RouteConfig(BaseModel):
    path: str
    methods: List[str]
    backend_service: str
    weight: float = 1.0
    enabled: bool = True
    metadata: Dict[str, Any] = {}

class TrafficPattern(BaseModel):
    route_path: str
    avg_requests: float
    peak_times: List[Dict[str, Any]]
    common_patterns: Dict[str, Any]
    analyzed_at: datetime = datetime.utcnow()

class GatewayMetrics(BaseModel):
    total_requests: int
    avg_latency: float
    error_rate: float
    bandwidth_usage: float
    active_connections: int
    collected_at: datetime

class GatewayConfig(BaseModel):
    name: str
    version: str
    routes: List[RoutePolicy]
    security_policies: Dict[str, Any]
    rate_limits: Dict[str, Any]
    transformations: List[Dict[str, Any]]
    enabled: bool = True

class RoutePolicy(BaseModel):
    id: str
    path_pattern: str
    methods: List[str]
    backend_service: str
    load_balancing: Dict[str, Any]
    circuit_breaker: Dict[str, Any]
    timeout: int
    retry_policy: Dict[str, Any]

class APIMetrics(BaseModel):
    route_id: str
    requests_count: int
    error_count: int
    latency_avg: float
    bandwidth_used: int
    last_updated: datetime 