from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class SmartContract(BaseModel):
    address: str
    abi: Dict[str, Any]
    name: str
    network: str

class BlockchainTransaction(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    value: float
    timestamp: datetime
    status: str

class NFTLicense(BaseModel):
    token_id: str
    owner: str
    metadata: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None 