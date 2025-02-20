from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime

class QuantumSafeConfig(BaseModel):
    enabled_algorithms: List[str]
    key_sizes: Dict[str, int]
    security_level: str
    post_quantum_ready: bool

class EncryptionResult(BaseModel):
    algorithm: str
    encrypted_data: bytes
    metadata: Dict[str, Any]
    timestamp: datetime = datetime.utcnow() 