from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class DeploymentConfig(BaseModel):
    deployment_id: str
    service_name: str
    version: str
    environment: str
    resources: Dict[str, Any]
    scaling_config: Dict[str, Any]
    dependencies: List[str]
    feature_flags: Dict[str, bool]

class DeploymentStrategy(BaseModel):
    strategy_type: str  # blue-green, canary, rolling
    phases: List[Dict[str, Any]]
    validation_steps: List[str]
    rollback_triggers: List[Dict[str, Any]]
    metrics_thresholds: Dict[str, float]

class DeploymentStatus(BaseModel):
    deployment_id: str
    status: str
    progress: float
    current_phase: str
    health_metrics: Dict[str, Any]
    logs: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]

class RollbackPlan(BaseModel):
    deployment_id: str
    rollback_steps: List[Dict[str, Any]]
    data_backup: Dict[str, Any]
    recovery_points: List[datetime]
    estimated_duration: int 