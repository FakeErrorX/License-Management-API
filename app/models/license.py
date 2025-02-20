from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class LicenseType(str, Enum):
    TRIAL = "trial"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class LicenseStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

class LicenseFeature(BaseModel):
    name: str
    enabled: bool
    max_usage: Optional[int] = None
    current_usage: Optional[int] = None

class LicenseBase(BaseModel):
    type: LicenseType
    features: List[LicenseFeature]
    max_activations: int = 1
    expiration_days: Optional[int] = None
    ip_restriction: Optional[List[str]] = None
    domain_restriction: Optional[List[str]] = None
    metadata: Optional[Dict] = None

class LicenseCreate(LicenseBase):
    user_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "standard",
                "features": [
                    {
                        "name": "basic_access",
                        "enabled": True
                    },
                    {
                        "name": "premium_feature",
                        "enabled": False
                    }
                ],
                "max_activations": 1,
                "expiration_days": 365,
                "user_id": "user123"
            }
        }

class BulkLicenseCreate(BaseModel):
    count: int = Field(..., gt=0, le=1000)
    license_data: LicenseCreate

class LicenseUpdate(BaseModel):
    type: Optional[LicenseType] = None
    features: Optional[List[LicenseFeature]] = None
    max_activations: Optional[int] = None
    expiration_date: Optional[datetime] = None
    status: Optional[LicenseStatus] = None
    metadata: Optional[Dict] = None

class License(LicenseBase):
    id: str
    key: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    expiration_date: Optional[datetime] = None
    last_check: Optional[datetime] = None
    status: LicenseStatus
    current_activations: int = 0
    activation_history: List[Dict] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "lic123",
                "key": "XXXX-YYYY-ZZZZ-WWWW",
                "type": "standard",
                "user_id": "user123",
                "features": [
                    {
                        "name": "basic_access",
                        "enabled": True
                    }
                ],
                "status": "active",
                "created_at": "2023-01-01T00:00:00Z",
                "expiration_date": "2024-01-01T00:00:00Z"
            }
        }

class LicenseValidation(BaseModel):
    is_valid: bool
    license_key: str
    status: LicenseStatus
    features: List[LicenseFeature]
    expiration_date: Optional[datetime] = None
    message: Optional[str] = None

class LicenseUsage(BaseModel):
    license_id: str
    feature_name: str
    timestamp: datetime
    usage_count: int
    metadata: Optional[Dict] = None

class LicenseAnalytics(BaseModel):
    total_activations: int
    active_devices: List[Dict]
    usage_history: List[LicenseUsage]
    feature_usage: Dict[str, int]
    last_validation: Optional[datetime] = None
