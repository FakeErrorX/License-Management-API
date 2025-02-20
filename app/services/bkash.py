import json
import httpx
from typing import Dict, Optional
from datetime import datetime
from fastapi import HTTPException

from app.core.config import settings
from app.models.payment import PaymentStatus, BkashPayment

class BkashService:
    def __init__(self):
        self.base_url = settings.BKASH_BASE_URL
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username = settings.BKASH_USERNAME
        self.password = settings.BKASH_PASSWORD
        self._token = None
        self._token_expiry = None

    async def _get_token(self) -> str:
        """Get or refresh bKash API token."""
        if self._token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._token

        headers = {
            "username": self.username,
            "password": self.password
        }
        data = {
            "app_key": self.app_key,
            "app_secret": self.app_secret
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tokenized/checkout/token/grant",
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to get bKash token"
                )

            result = response.json()
            self._token = result["id_token"]
            # Token typically expires in 1 hour
            self._token_expiry = datetime.now() + timedelta(minutes=55)
            return self._token

    async def create_payment(self, amount: float, invoice_number: str) -> Dict:
        """Create a bKash payment request."""
        token = await self._get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-APP-Key": self.app_key
        }
        
        data = {
            "mode": "0011",
            "payerReference": invoice_number,
            "callbackURL": f"{settings.API_URL}/api/v1/payments/bkash/callback",
            "amount": str(amount),
            "currency": "BDT",
            "intent": "sale",
            "merchantInvoiceNumber": invoice_number
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tokenized/checkout/create",
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to create bKash payment"
                )

            return response.json()

    async def execute_payment(self, payment_id: str) -> Dict:
        """Execute a bKash payment after user confirmation."""
        token = await self._get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-APP-Key": self.app_key
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tokenized/checkout/execute",
                headers=headers,
                json={"paymentID": payment_id}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to execute bKash payment"
                )

            return response.json()

    async def query_payment(self, payment_id: str) -> Dict:
        """Query the status of a bKash payment."""
        token = await self._get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-APP-Key": self.app_key
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tokenized/checkout/payment/status",
                headers=headers,
                json={"paymentID": payment_id}
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to query bKash payment status"
                )

            return response.json()

    async def refund_payment(
        self, 
        payment_id: str, 
        amount: float,
        reason: str
    ) -> Dict:
        """Refund a bKash payment."""
        token = await self._get_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "X-APP-Key": self.app_key
        }

        data = {
            "paymentID": payment_id,
            "amount": str(amount),
            "trxID": payment_id,
            "sku": "RefundedOrder",
            "reason": reason
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/tokenized/checkout/payment/refund",
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to refund bKash payment"
                )

            return response.json()
