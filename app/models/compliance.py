from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class ComplianceRule(BaseModel):
    id: str
    name: str
    description: str
    rule_type: str
    parameters: Dict[str, Any]
    severity: str
    enabled: bool = True

class ComplianceViolation(BaseModel):
    rule_id: str
    severity: str
    description: str
    affected_data: Dict[str, Any]
    suggested_fix: Optional[str]

class ComplianceCheck(BaseModel):
    data_id: str
    rule_type: str
    violations: List[ComplianceViolation]
    timestamp: datetime

class ComplianceReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_checks: int
    violations_found: int
    insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    generated_at: datetime = datetime.utcnow() 