from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class RateLimit(BaseModel):
    id: str
    name: str
    requests_per_second: int
    burst_size: int
    user_type: str
    service_tier: str
    adaptive: bool = True

class RateLimitPolicy(BaseModel):
    id: str
    name: str
    rules: List[Dict[str, Any]]
    fallback_action: str
    notification_threshold: float
    cooldown_period: int

class QuotaUsage(BaseModel):
    user_id: str
    service_id: str
    current_usage: int
    quota_limit: int
    reset_time: datetime
    last_updated: datetime

class RateLimitMetrics(BaseModel):
    policy_id: str
    requests_allowed: int
    requests_denied: int
    current_rate: float
    burst_events: int
    last_updated: datetime 