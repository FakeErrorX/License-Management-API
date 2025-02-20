from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class APIVersion(BaseModel):
    version: str
    release_date: datetime
    status: str  # active, deprecated, sunset
    features: List[str]
    breaking_changes: List[Dict[str, Any]]
    supported_until: Optional[datetime]

class VersionMigration(BaseModel):
    from_version: str
    to_version: str
    migration_steps: List[Dict[str, Any]]
    automated: bool
    estimated_effort: str
    created_at: datetime

class VersionCompatibility(BaseModel):
    version: str
    compatible_versions: List[str]
    breaking_changes: List[Dict[str, Any]]
    timestamp: datetime

class VersionConfig(BaseModel):
    version: str
    release_type: str  # major, minor, patch
    api_changes: List[Dict[str, Any]]
    compatibility_mode: bool
    grace_period: int
    notification_config: Dict[str, Any]

class MigrationPlan(BaseModel):
    from_version: str
    to_version: str
    steps: List[Dict[str, Any]]
    estimated_effort: str
    breaking_changes: List[Dict[str, Any]]
    rollback_plan: Dict[str, Any]
    created_at: datetime

class VersionMetrics(BaseModel):
    version: str
    active_users: int
    request_count: int
    error_rate: float
    usage_trend: Dict[str, float]
    collected_at: datetime 