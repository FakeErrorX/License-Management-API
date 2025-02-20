from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class CloudProvider(BaseModel):
    id: str
    name: str  # AWS, GCP, Azure
    credentials: Dict[str, str]
    regions: List[str]
    services: List[str]

class CloudDeployment(BaseModel):
    id: str
    provider_id: str
    service_name: str
    config: Dict[str, Any]
    region: str
    replicas: int
    deployed_at: datetime
    status: str

class DeploymentStatus(BaseModel):
    deployment_id: str
    success: bool
    status: str
    details: Dict[str, Any]
    timestamp: datetime 