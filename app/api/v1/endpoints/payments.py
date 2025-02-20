from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any, Dict, List
from app.core.security import oauth2_scheme
from app.services.auth import AuthService
from app.services.payments import PaymentService
from app.models.payment import (
    PaymentCreate,
    PaymentUpdate,
    SubscriptionCreate,
    PaymentMethod,
    Invoice
)

router = APIRouter()
auth_service = AuthService()
payment_service = PaymentService()

@router.post("/create")
async def create_payment(
    request: Request,
    payment: PaymentCreate,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Create a new payment.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.create_payment(current_user, payment)

@router.post("/subscription")
async def create_subscription(
    request: Request,
    subscription: SubscriptionCreate,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Create a new subscription.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.create_subscription(current_user, subscription)

@router.post("/methods")
async def add_payment_method(
    request: Request,
    payment_method: PaymentMethod,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Add a new payment method.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.add_payment_method(current_user, payment_method)

@router.get("/methods")
async def get_payment_methods(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get all payment methods for a user.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.get_payment_methods(current_user)

@router.post("/crypto")
async def process_crypto_payment(
    request: Request,
    payment: PaymentCreate,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Process a cryptocurrency payment.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.process_crypto_payment(current_user, payment)

@router.get("/invoices")
async def get_invoices(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> List[Invoice]:
    """
    Get all invoices for a user.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.get_invoices(current_user)

@router.post("/invoices/{invoice_id}/pay")
async def pay_invoice(
    request: Request,
    invoice_id: str,
    payment_method_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Pay a specific invoice.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.pay_invoice(current_user, invoice_id, payment_method_id)

@router.post("/refund/{payment_id}")
async def process_refund(
    request: Request,
    payment_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Process a refund for a payment.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.process_refund(current_user, payment_id)

@router.get("/subscriptions")
async def get_subscriptions(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get all subscriptions for a user.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.get_subscriptions(current_user)

@router.post("/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(
    request: Request,
    subscription_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Cancel a subscription.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.cancel_subscription(current_user, subscription_id)

@router.post("/usage-based")
async def record_usage_based_billing(
    request: Request,
    usage_data: Dict,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Record usage for usage-based billing.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.record_usage_billing(current_user, usage_data)

@router.get("/pricing")
async def get_pricing_tiers(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get available pricing tiers.
    """
    return await payment_service.get_pricing_tiers()

@router.post("/affiliate/register")
async def register_affiliate(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Register as an affiliate.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.register_affiliate(current_user)

@router.get("/affiliate/earnings")
async def get_affiliate_earnings(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get affiliate earnings and statistics.
    """
    current_user = await auth_service.get_current_user(token)
    return await payment_service.get_affiliate_earnings(current_user)
