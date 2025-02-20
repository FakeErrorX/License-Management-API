from fastapi import APIRouter, Request, HTTPException, status, Depends
from typing import Any, Dict
from app.services.webhooks import WebhookService
from app.core.security import oauth2_scheme
from app.services.auth import AuthService

router = APIRouter()
webhook_service = WebhookService()
auth_service = AuthService()

@router.post("/stripe")
async def stripe_webhook(request: Request) -> Dict:
    """
    Handle Stripe webhook events.
    """
    signature = request.headers.get("Stripe-Signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature"
        )
    
    payload = await request.body()
    return await webhook_service.handle_stripe_webhook(payload, signature)

@router.post("/paypal")
async def paypal_webhook(request: Request) -> Dict:
    """
    Handle PayPal webhook events.
    """
    payload = await request.json()
    return await webhook_service.handle_paypal_webhook(payload)

@router.post("/crypto")
async def crypto_webhook(request: Request) -> Dict:
    """
    Handle cryptocurrency payment webhook events.
    """
    payload = await request.json()
    return await webhook_service.handle_crypto_webhook(payload)

@router.post("/license-events")
async def license_webhook(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Handle license-related webhook events.
    """
    current_user = await auth_service.get_current_user(token)
    payload = await request.json()
    return await webhook_service.handle_license_webhook(current_user, payload)

@router.post("/register")
async def register_webhook(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Register a new webhook endpoint.
    """
    current_user = await auth_service.get_current_user(token)
    payload = await request.json()
    return await webhook_service.register_webhook(current_user, payload)

@router.get("/endpoints")
async def get_webhook_endpoints(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get registered webhook endpoints.
    """
    current_user = await auth_service.get_current_user(token)
    return await webhook_service.get_webhook_endpoints(current_user)

@router.delete("/endpoints/{endpoint_id}")
async def delete_webhook_endpoint(
    request: Request,
    endpoint_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Delete a webhook endpoint.
    """
    current_user = await auth_service.get_current_user(token)
    return await webhook_service.delete_webhook_endpoint(current_user, endpoint_id)

@router.get("/logs")
async def get_webhook_logs(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get webhook delivery logs.
    """
    current_user = await auth_service.get_current_user(token)
    return await webhook_service.get_webhook_logs(current_user)

@router.post("/test/{endpoint_id}")
async def test_webhook(
    request: Request,
    endpoint_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Send a test webhook event.
    """
    current_user = await auth_service.get_current_user(token)
    return await webhook_service.test_webhook(current_user, endpoint_id)

@router.post("/retry/{event_id}")
async def retry_webhook(
    request: Request,
    event_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Retry a failed webhook delivery.
    """
    current_user = await auth_service.get_current_user(token)
    return await webhook_service.retry_webhook(current_user, event_id)
