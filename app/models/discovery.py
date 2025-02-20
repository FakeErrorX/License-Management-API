from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class ServiceInstance(BaseModel):
    service_id: str
    name: str
    version: str
    endpoints: List[str]
    metadata: Dict[str, Any]
    registered_at: datetime
    last_seen: datetime

class HealthStatus(BaseModel):
    service_id: str
    status: str
    response_time: float
    error_rate: float
    resource_usage: Dict[str, float]
    dependencies_health: Dict[str, bool]
    last_check: datetime

class ServiceDependency(BaseModel):
    service_id: str
    depends_on: List[str]
    dependency_type: str
    criticality: str
    fallback_options: List[str]

class ServiceRegistry(BaseModel):
    services: Dict[str, ServiceInstance]
    dependencies: Dict[str, ServiceDependency]
    health_checks: Dict[str, HealthStatus]
    last_updated: datetime 