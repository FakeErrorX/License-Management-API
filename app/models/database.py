from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from bson import ObjectId

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    RESELLER = "reseller"
    AFFILIATE = "affiliate"

class AuthProvider(str, Enum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"

class LicenseType(str, Enum):
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CANCELLED = "cancelled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"

# User Management Collections
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    email: EmailStr
    username: str
    password_hash: Optional[str]
    role: UserRole
    is_active: bool = True
    is_verified: bool = False
    auth_provider: AuthProvider
    auth_provider_id: Optional[str]
    stripe_customer_id: Optional[str]
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str]
    api_key: Optional[str]
    api_secret_hash: Optional[str]
    last_login: Optional[datetime]
    login_attempts: int = 0
    locked_until: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict = Field(default_factory=dict)

class UserDevice(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    device_id: str
    device_name: str
    device_type: str
    is_trusted: bool = False
    last_used: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    session_token: str
    device_id: Optional[str]
    ip_address: str
    user_agent: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

# License Management Collections
class License(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    key: str
    user_id: str
    type: LicenseType
    features: List[str]
    max_devices: int
    max_api_calls: Optional[int]
    is_active: bool = True
    activation_date: Optional[datetime]
    expiration_date: Optional[datetime]
    last_checked: Optional[datetime]
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class LicenseActivation(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    license_id: str
    device_id: str
    ip_address: str
    activation_code: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LicenseUsage(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    license_id: str
    endpoint: str
    request_count: int
    bytes_transferred: int
    date: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Payment and Subscription Collections
class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime]
    payment_method_id: str
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Payment(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    subscription_id: Optional[str]
    amount: float
    currency: str
    provider: PaymentProvider
    provider_payment_id: str
    status: PaymentStatus
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PaymentMethod(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    provider: PaymentProvider
    provider_method_id: str
    last_4: Optional[str]
    expiry_month: Optional[int]
    expiry_year: Optional[int]
    is_default: bool = False
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# API Management Collections
class APIKey(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    key: str
    secret_hash: str
    name: str
    permissions: List[str]
    rate_limit: Optional[int]
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class APIUsage(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    api_key_id: str
    endpoint: str
    method: str
    response_time: float
    status_code: int
    ip_address: str
    user_agent: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Security Collections
class SecurityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: Optional[str]
    event_type: str
    ip_address: str
    user_agent: str
    details: Dict
    severity: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BlockedIP(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    ip_address: str
    reason: str
    blocked_until: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Monitoring Collections
class Metric(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    value: float
    tags: Dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    condition: str
    threshold: float
    status: str
    last_triggered: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Webhook Collections
class Webhook(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    url: str
    events: List[str]
    secret: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class WebhookDelivery(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    webhook_id: str
    event_type: str
    payload: Dict
    response_code: Optional[int]
    response_body: Optional[str]
    delivery_attempts: int = 0
    last_attempt: Optional[datetime]
    created_at: datetime = Field(default_factory=datetime.utcnow)

# AI/ML Collections
class MLModel(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    version: str
    type: str
    metrics: Dict
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MLPrediction(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    model_id: str
    input_data: Dict
    prediction: Dict
    confidence: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Reseller and Affiliate Collections
class Reseller(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    company_name: str
    commission_rate: float
    total_sales: float = 0
    is_active: bool = True
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Affiliate(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    affiliate_code: str
    commission_rate: float
    total_earnings: float = 0
    is_active: bool = True
    metadata: Dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Audit Collections
class AuditLog(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: str
    changes: Dict
    ip_address: str
    user_agent: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Documentation Collections
class APIDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    endpoint: str
    method: str
    version: str
    description: str
    parameters: List[Dict]
    responses: Dict
    examples: Dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Cache Collections
class CacheEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    key: str
    value: Dict
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

# System Settings Collections
class SystemSetting(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    key: str
    value: Dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Feature Flag Collections
class FeatureFlag(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    description: str
    is_enabled: bool = False
    rules: Dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
