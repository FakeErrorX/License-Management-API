from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class ServiceInstance(BaseModel):
    id: str
    name: str
    version: str
    endpoints: List[str]
    health_status: str
    metadata: Dict[str, Any]
    last_seen: datetime

class TrafficPolicy(BaseModel):
    id: str
    service_id: str
    load_balancing: Dict[str, Any]
    circuit_breaker: Dict[str, Any]
    timeout_ms: int
    retry_policy: Dict[str, Any]
    fault_tolerance: Dict[str, Any]

class ServiceMeshConfig(BaseModel):
    mesh_id: str
    version: str
    discovery_config: Dict[str, Any]
    mtls_config: Dict[str, Any]
    observability_config: Dict[str, Any]
    policy_defaults: Dict[str, Any] 