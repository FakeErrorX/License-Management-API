from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

class VoiceCommand(BaseModel):
    id: str
    raw_text: str
    parsed_intent: str
    parameters: Dict[str, Any]
    confidence_score: float
    timestamp: datetime

class VoiceResponse(BaseModel):
    command_id: str
    success: bool
    response_text: str
    response_data: Optional[Dict[str, Any]]
    audio_response: Optional[bytes]
    timestamp: datetime 