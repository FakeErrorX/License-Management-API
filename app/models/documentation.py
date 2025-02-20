from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class APIEndpoint(BaseModel):
    path: str
    method: str
    description: str
    parameters: Dict[str, Any]
    response_schema: Dict[str, Any]

class Documentation(BaseModel):
    endpoint: str
    description: str
    parameters: List[Dict[str, Any]]
    examples: List[Dict[str, Any]]
    generated_at: datetime
    last_updated: Optional[datetime] = None

class InteractiveGuide(BaseModel):
    guide_id: str
    title: str
    steps: List[Dict[str, Any]]
    difficulty_level: str
    estimated_time: int
    created_at: datetime

class CodeExample(BaseModel):
    language: str
    code: str
    description: str
    tags: List[str]
    created_at: datetime

class DocTemplate(BaseModel):
    template_id: str
    template_type: str
    structure: Dict[str, Any]
    placeholders: List[str]
    style_guide: Dict[str, Any]
    created_at: datetime

class APIEndpointDoc(BaseModel):
    endpoint_path: str
    http_method: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Any]
    examples: List[CodeExample]
    notes: List[str]

class ErrorDoc(BaseModel):
    error_code: str
    description: str
    possible_causes: List[str]
    solutions: List[str]
    examples: List[Dict[str, Any]]
    related_errors: List[str] 