from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class ResourceMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    network_io: float
    disk_io: float
    request_count: int
    error_rate: float
    latency: float
    timestamp: datetime

class LoadPrediction(BaseModel):
    service_id: str
    predictions: Dict[str, List[float]]  # Metrics -> predicted values
    confidence_intervals: Dict[str, List[Dict[str, float]]]
    recommendations: List[Dict[str, Any]]
    generated_at: datetime

class ScalingRecommendation(BaseModel):
    service_id: str
    current_instances: int
    recommended_instances: int
    confidence_score: float
    factors: List[Dict[str, Any]]
    valid_until: datetime 