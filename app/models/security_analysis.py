from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class SecurityScan(BaseModel):
    scan_id: str
    scan_type: str
    target_components: List[str]
    scan_depth: str
    findings: List[Dict[str, Any]]
    scan_status: str
    started_at: datetime
    completed_at: Optional[datetime]

class Vulnerability(BaseModel):
    vuln_id: str
    severity: str
    category: str
    description: str
    affected_components: List[str]
    exploit_potential: float
    mitigation_steps: List[str]
    discovered_at: datetime

class AttackPattern(BaseModel):
    pattern_id: str
    pattern_type: str
    frequency: int
    success_rate: float
    target_vectors: List[str]
    countermeasures: List[str]
    last_seen: datetime

class SecurityReport(BaseModel):
    report_id: str
    risk_score: float
    critical_vulnerabilities: int
    high_vulnerabilities: int
    attack_surface_analysis: Dict[str, Any]
    compliance_status: Dict[str, bool]
    recommendations: List[Dict[str, Any]]
    generated_at: datetime 