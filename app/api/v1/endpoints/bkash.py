from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.payment import PaymentCreate, PaymentUpdate
from app.services.payments import PaymentService
from app.api.deps import get_current_user, get_payment_service

router = APIRouter()

@router.post("/create")
async def create_bkash_payment(
    payment: PaymentCreate,
    current_user = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict:
    """Create a new bKash payment."""
    if payment.provider != "bkash":
        raise HTTPException(
            status_code=400,
            detail="Invalid payment provider. Must be 'bkash'"
        )
    return await payment_service.create_payment(current_user, payment)

@router.post("/execute/{payment_id}")
async def execute_bkash_payment(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict:
    """Execute a bKash payment after user confirmation."""
    return await payment_service.execute_bkash_payment(payment_id)

@router.get("/status/{payment_id}")
async def get_bkash_payment_status(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict:
    """Get the status of a bKash payment."""
    return await payment_service.query_bkash_payment(payment_id)

@router.post("/refund/{payment_id}")
async def refund_bkash_payment(
    payment_id: str,
    amount: float = Query(..., gt=0),
    reason: str = Query("Customer requested refund"),
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict:
    """Refund a bKash payment."""
    return await payment_service.refund_bkash_payment(
        payment_id=payment_id,
        amount=amount,
        reason=reason
    )

@router.post("/webhook")
async def handle_bkash_webhook(
    payload: Dict,
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict:
    """Handle bKash webhook notifications."""
    # Implementation depends on bKash webhook structure
    # This is a placeholder that should be implemented based on bKash's webhook documentation
    return {"status": "success"}
