from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class TestCase(BaseModel):
    id: str
    name: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    created_at: datetime

class TestResult(BaseModel):
    test_case_id: str
    status: str
    actual_output: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: float
    executed_at: datetime

class TestSuite(BaseModel):
    name: str
    endpoint: APIEndpoint
    test_cases: List[TestCase]
    created_at: datetime = datetime.utcnow()

class TestCoverage(BaseModel):
    endpoint_id: str
    coverage_percentage: float
    covered_paths: List[str]
    uncovered_paths: List[str]
    risk_areas: List[Dict[str, Any]]
    last_updated: datetime 