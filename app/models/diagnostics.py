from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class ErrorPattern(BaseModel):
    pattern_id: str
    error_type: str
    stack_trace_pattern: str
    frequency: int
    context_parameters: Dict[str, Any]
    first_seen: datetime
    last_seen: datetime

class ErrorSolution(BaseModel):
    solution_id: str
    error_pattern_id: str
    description: str
    steps: List[str]
    success_rate: float
    implementation_time: str
    created_at: datetime

class DiagnosisResult(BaseModel):
    error_id: str
    error_type: str
    patterns_matched: List[ErrorPattern]
    suggested_solutions: List[ErrorSolution]
    confidence_score: float
    analyzed_at: datetime 