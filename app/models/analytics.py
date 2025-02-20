from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class APIMetrics(BaseModel):
    response_time: float
    status_code: int
    ip_address: str
    geo_location: Optional[Dict[str, str]]
    request_size: int
    response_size: int

class UsageStats(BaseModel):
    total_calls: int = 0
    avg_response_time: float = 0.0
    total_data_transfer: int = 0

class APIUsageMetrics(BaseModel):
    endpoint_id: str
    total_requests: int
    unique_users: int
    avg_response_time: float
    error_rate: float
    peak_usage_times: List[datetime]
    usage_by_version: Dict[str, int]
    collected_at: datetime

class UserBehavior(BaseModel):
    user_id: str
    session_duration: float
    endpoints_accessed: List[str]
    common_patterns: List[Dict[str, Any]]
    error_encounters: List[Dict[str, Any]]
    last_active: datetime

class PerformanceInsight(BaseModel):
    insight_id: str
    category: str  # performance, security, usage, etc.
    severity: str
    description: str
    affected_components: List[str]
    recommendations: List[str]
    detected_at: datetime

class UsageTrend(BaseModel):
    metric_name: str
    current_value: float
    predicted_value: float
    confidence: float
    trend_direction: str
    factors: List[Dict[str, Any]] 