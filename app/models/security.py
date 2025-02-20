from enum import Enum
from pydantic import BaseModel
from typing import Dict, Any, List
from datetime import datetime

class ThreatLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class SecurityThreat(BaseModel):
    threat_level: ThreatLevel
    score: float = 0.0
    details: Dict[str, Any] = {}

class SecurityEvent(BaseModel):
    event_id: str
    event_type: str
    severity: str
    source_ip: str
    user_agent: str
    payload: Dict[str, Any]
    timestamp: datetime

class ThreatDetection(BaseModel):
    threat_id: str
    type: str
    severity: str
    confidence_score: float
    affected_components: List[str]
    mitigation_steps: List[str]
    detected_at: datetime 