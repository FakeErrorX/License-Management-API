from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class TuningConfig(BaseModel):
    service_id: str
    target_metrics: Dict[str, float]
    optimization_priorities: List[str]
    constraints: Dict[str, Any]
    auto_apply: bool = False

class PerformanceProfile(BaseModel):
    service_id: str
    cpu_profile: Dict[str, Any]
    memory_profile: Dict[str, Any]
    io_profile: Dict[str, Any]
    network_profile: Dict[str, Any]
    bottlenecks: List[Dict[str, Any]]
    collected_at: datetime

class OptimizationResult(BaseModel):
    service_id: str
    optimizations_applied: List[Dict[str, Any]]
    performance_improvement: float
    bottlenecks_resolved: List[str]
    side_effects: List[Dict[str, Any]]
    applied_at: datetime 