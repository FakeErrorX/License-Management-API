from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import stripe
import hmac
import hashlib
import json
from bson import ObjectId

from app.core.config import settings
from app.models.auth import UserInDB

class WebhookService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.webhooks = self.db.webhooks
        self.webhook_logs = self.db.webhook_logs

    async def handle_stripe_webhook(self, payload: bytes, signature: str) -> Dict:
        """
        Handle incoming Stripe webhook events.
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Log webhook event
            await self._log_webhook_event("stripe", event)
            
            # Handle different event types
            if event.type == "payment_intent.succeeded":
                await self._handle_payment_success(event.data.object)
            elif event.type == "payment_intent.payment_failed":
                await self._handle_payment_failure(event.data.object)
            elif event.type == "customer.subscription.updated":
                await self._handle_subscription_update(event.data.object)
            
            return {"status": "success"}
        except Exception as e:
            await self._log_webhook_error("stripe", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def handle_paypal_webhook(self, payload: Dict) -> Dict:
        """
        Handle incoming PayPal webhook events.
        """
        try:
            # Verify PayPal webhook signature (implementation depends on PayPal SDK)
            
            # Log webhook event
            await self._log_webhook_event("paypal", payload)
            
            event_type = payload.get("event_type")
            
            if event_type == "PAYMENT.CAPTURE.COMPLETED":
                await self._handle_paypal_payment_success(payload)
            elif event_type == "PAYMENT.CAPTURE.DENIED":
                await self._handle_paypal_payment_failure(payload)
            
            return {"status": "success"}
        except Exception as e:
            await self._log_webhook_error("paypal", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def handle_crypto_webhook(self, payload: Dict) -> Dict:
        """
        Handle incoming cryptocurrency payment webhook events.
        """
        try:
            # Verify crypto webhook signature
            
            # Log webhook event
            await self._log_webhook_event("crypto", payload)
            
            transaction_status = payload.get("status")
            
            if transaction_status == "confirmed":
                await self._handle_crypto_payment_success(payload)
            elif transaction_status == "failed":
                await self._handle_crypto_payment_failure(payload)
            
            return {"status": "success"}
        except Exception as e:
            await self._log_webhook_error("crypto", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def handle_license_webhook(self, user: UserInDB, payload: Dict) -> Dict:
        """
        Handle license-related webhook events.
        """
        try:
            # Verify user has permission to send webhook
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User not active"
                )
            
            # Log webhook event
            await self._log_webhook_event("license", payload)
            
            event_type = payload.get("event_type")
            
            if event_type == "license.created":
                await self._handle_license_created(payload)
            elif event_type == "license.expired":
                await self._handle_license_expired(payload)
            elif event_type == "license.revoked":
                await self._handle_license_revoked(payload)
            
            return {"status": "success"}
        except Exception as e:
            await self._log_webhook_error("license", str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def register_webhook(self, user: UserInDB, payload: Dict) -> Dict:
        """
        Register a new webhook endpoint.
        """
        try:
            webhook = {
                "user_id": str(user.id),
                "url": payload["url"],
                "events": payload["events"],
                "description": payload.get("description"),
                "secret": self._generate_webhook_secret(),
                "created_at": datetime.utcnow(),
                "is_active": True
            }
            
            result = await self.webhooks.insert_one(webhook)
            webhook["id"] = str(result.inserted_id)
            
            return webhook
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def get_webhook_endpoints(self, user: UserInDB) -> List[Dict]:
        """
        Get registered webhook endpoints.
        """
        webhooks = await self.webhooks.find(
            {"user_id": str(user.id)}
        ).to_list(None)
        
        return [{**hook, "id": str(hook["_id"])} for hook in webhooks]

    async def delete_webhook_endpoint(self, user: UserInDB, endpoint_id: str) -> Dict:
        """
        Delete a webhook endpoint.
        """
        result = await self.webhooks.delete_one({
            "_id": ObjectId(endpoint_id),
            "user_id": str(user.id)
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found"
            )
        
        return {"status": "success"}

    async def get_webhook_logs(self, user: UserInDB) -> List[Dict]:
        """
        Get webhook delivery logs.
        """
        logs = await self.webhook_logs.find(
            {"user_id": str(user.id)}
        ).sort("timestamp", -1).limit(100).to_list(None)
        
        return [{**log, "id": str(log["_id"])} for log in logs]

    async def test_webhook(self, user: UserInDB, endpoint_id: str) -> Dict:
        """
        Send a test webhook event.
        """
        webhook = await self.webhooks.find_one({
            "_id": ObjectId(endpoint_id),
            "user_id": str(user.id)
        })
        
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found"
            )
        
        # Send test event
        test_payload = {
            "event_type": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "This is a test webhook event"}
        }
        
        await self._send_webhook(webhook, test_payload)
        
        return {"status": "success"}

    async def retry_webhook(self, user: UserInDB, event_id: str) -> Dict:
        """
        Retry a failed webhook delivery.
        """
        event = await self.webhook_logs.find_one({
            "_id": ObjectId(event_id),
            "user_id": str(user.id),
            "status": "failed"
        })
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed webhook event not found"
            )
        
        webhook = await self.webhooks.find_one({
            "_id": ObjectId(event["webhook_id"])
        })
        
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook endpoint not found"
            )
        
        # Retry webhook delivery
        await self._send_webhook(webhook, event["payload"])
        
        return {"status": "success"}

    async def _log_webhook_event(self, provider: str, event: Dict) -> None:
        """
        Log a webhook event.
        """
        log = {
            "provider": provider,
            "event": event,
            "timestamp": datetime.utcnow(),
            "status": "received"
        }
        
        await self.webhook_logs.insert_one(log)

    async def _log_webhook_error(self, provider: str, error: str) -> None:
        """
        Log a webhook error.
        """
        log = {
            "provider": provider,
            "error": error,
            "timestamp": datetime.utcnow(),
            "status": "error"
        }
        
        await self.webhook_logs.insert_one(log)

    def _generate_webhook_secret(self) -> str:
        """
        Generate a secure webhook secret.
        """
        return hmac.new(
            settings.API_KEY_SALT.encode(),
            str(datetime.utcnow().timestamp()).encode(),
            hashlib.sha256
        ).hexdigest()

    async def _send_webhook(self, webhook: Dict, payload: Dict) -> None:
        """
        Send webhook to registered endpoint.
        """
        # Implementation would use httpx or similar to send webhook
        # This is a placeholder
        pass

    async def _handle_payment_success(self, payment: Dict) -> None:
        """
        Handle successful payment webhook.
        """
        # Implementation would update payment status and trigger related actions
        pass

    async def _handle_payment_failure(self, payment: Dict) -> None:
        """
        Handle failed payment webhook.
        """
        # Implementation would update payment status and notify user
        pass

    async def _handle_subscription_update(self, subscription: Dict) -> None:
        """
        Handle subscription update webhook.
        """
        # Implementation would update subscription status
        pass
