from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    BKASH = "bkash"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class PaymentMethod(BaseModel):
    id: str
    provider: PaymentProvider
    type: str
    details: dict

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    provider: PaymentProvider
    payment_method_id: Optional[str] = None
    return_url: Optional[str] = None
    metadata: Optional[dict] = None

class PaymentUpdate(BaseModel):
    status: PaymentStatus
    transaction_id: Optional[str] = None
    metadata: Optional[dict] = None

class BkashPayment(BaseModel):
    payment_id: str
    amount: float
    currency: str = "BDT"
    status: PaymentStatus
    customer_msisdn: str
    transaction_id: Optional[str] = None
    payment_execute_time: Optional[str] = None
    merchant_invoice_number: Optional[str] = None
