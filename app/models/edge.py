from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class EdgeNode(BaseModel):
    id: str
    name: str
    location: Dict[str, float]  # lat, long
    capabilities: Dict[str, Any]
    status: str
    last_seen: datetime

class EdgeDeployment(BaseModel):
    id: str
    node_id: str
    service_name: str
    config: Dict[str, Any]
    deployed_at: datetime
    status: str
    health: str

class EdgeMetrics(BaseModel):
    node_id: str
    cpu_usage: float
    memory_usage: float
    network_bandwidth: float
    active_connections: int
    latency: float
    collected_at: datetime 