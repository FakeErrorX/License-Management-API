from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class BackupConfig(BaseModel):
    system_id: str
    backup_type: str  # full, incremental, differential
    compression_level: int
    encryption_enabled: bool
    retention_period: int
    schedule: Dict[str, Any]
    storage_location: str

class BackupJob(BaseModel):
    job_id: str
    config_id: str
    status: str
    progress: float
    size: int
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

class RestorePoint(BaseModel):
    point_id: str
    backup_job_id: str
    system_state: Dict[str, Any]
    size: int
    can_restore: bool
    created_at: datetime
    expires_at: datetime 