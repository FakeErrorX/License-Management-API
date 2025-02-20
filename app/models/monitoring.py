from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class PerformanceMetrics(BaseModel):
    service_id: str
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float
    response_times: List[float]
    error_rates: Dict[str, float]
    collected_at: datetime

class Alert(BaseModel):
    alert_id: str
    severity: str
    message: str
    metrics: Dict[str, Any]
    triggered_at: datetime
    resolved_at: Optional[datetime]

class MonitoringConfig(BaseModel):
    metrics_interval: int
    alert_thresholds: Dict[str, float]
    notification_channels: List[str]
    retention_period: int 