from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import stripe
import paypalrestsdk
from web3 import Web3
import redis
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
from decimal import Decimal

from app.core.config import settings

class PaymentService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.payments = self.db.payments
        self.subscriptions = self.db.subscriptions
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize payment providers
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })
        
        self.web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))

    async def process_payment(
        self,
        payment_data: Dict,
        provider: str = "stripe"
    ) -> Dict:
        """
        Process payment using specified provider.
        """
        try:
            # Validate payment data
            validated_data = await self.validate_payment_data(payment_data)
            
            # Process with provider
            if provider == "stripe":
                result = await self.process_stripe_payment(validated_data)
            elif provider == "paypal":
                result = await self.process_paypal_payment(validated_data)
            elif provider == "crypto":
                result = await self.process_crypto_payment(validated_data)
            else:
                raise ValueError("Invalid payment provider")
            
            # Record payment
            await self.record_payment(result)
            
            return {
                "payment_id": result["payment_id"],
                "status": result["status"],
                "amount": result["amount"],
                "currency": result["currency"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Payment processing failed: {str(e)}"
            )

    async def manage_subscription(
        self,
        action: str,
        subscription_data: Dict
    ) -> Dict:
        """
        Manage API subscription.
        """
        try:
            if action == "create":
                result = await self.create_subscription(subscription_data)
            elif action == "update":
                result = await self.update_subscription(subscription_data)
            elif action == "cancel":
                result = await self.cancel_subscription(subscription_data)
            else:
                raise ValueError("Invalid action")
            
            return {
                "subscription_id": result["subscription_id"],
                "status": result["status"],
                "details": result["details"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Subscription operation failed: {str(e)}"
            )

    async def generate_invoice(
        self,
        user_id: str,
        items: List[Dict]
    ) -> Dict:
        """
        Generate API usage invoice.
        """
        try:
            # Calculate charges
            charges = await self.calculate_charges(user_id, items)
            
            # Generate invoice
            invoice = await self.create_invoice(user_id, charges)
            
            # Store invoice
            await self.store_invoice(invoice)
            
            return {
                "invoice_id": invoice["invoice_id"],
                "amount": invoice["amount"],
                "items": invoice["items"],
                "due_date": invoice["due_date"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invoice generation failed: {str(e)}"
            )

    async def process_reseller_payment(
        self,
        reseller_id: str,
        payment_data: Dict
    ) -> Dict:
        """
        Process payment with reseller commission.
        """
        try:
            # Calculate commission
            commission = await self.calculate_commission(reseller_id, payment_data)
            
            # Process payment
            payment = await self.process_payment(payment_data)
            
            # Process commission
            await self.process_commission(reseller_id, commission)
            
            return {
                "payment_id": payment["payment_id"],
                "commission_id": commission["commission_id"],
                "amounts": {
                    "total": payment["amount"],
                    "commission": commission["amount"]
                },
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Reseller payment failed: {str(e)}"
            )

    async def manage_pricing_tier(
        self,
        action: str,
        tier_data: Dict
    ) -> Dict:
        """
        Manage API pricing tiers.
        """
        try:
            if action == "create":
                result = await self.create_pricing_tier(tier_data)
            elif action == "update":
                result = await self.update_pricing_tier(tier_data)
            elif action == "delete":
                result = await self.delete_pricing_tier(tier_data)
            else:
                raise ValueError("Invalid action")
            
            return {
                "tier_id": result["tier_id"],
                "status": result["status"],
                "details": result["details"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Pricing tier operation failed: {str(e)}"
            )

    async def process_affiliate_payment(
        self,
        affiliate_id: str,
        referral_data: Dict
    ) -> Dict:
        """
        Process affiliate referral payment.
        """
        try:
            # Validate referral
            validated_data = await self.validate_referral(affiliate_id, referral_data)
            
            # Calculate commission
            commission = await self.calculate_affiliate_commission(validated_data)
            
            # Process payment
            payment = await self.process_commission_payment(commission)
            
            return {
                "referral_id": validated_data["referral_id"],
                "payment_id": payment["payment_id"],
                "commission": commission["amount"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Affiliate payment failed: {str(e)}"
            )

    async def track_api_usage(
        self,
        user_id: str,
        usage_data: Dict
    ) -> Dict:
        """
        Track API usage for billing.
        """
        try:
            # Process usage data
            processed_data = await self.process_usage_data(usage_data)
            
            # Calculate charges
            charges = await self.calculate_usage_charges(processed_data)
            
            # Update usage records
            await self.update_usage_records(user_id, processed_data, charges)
            
            return {
                "user_id": user_id,
                "usage": processed_data,
                "charges": charges,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Usage tracking failed: {str(e)}"
            )

    async def process_stripe_payment(self, payment_data: Dict) -> Dict:
        """
        Process payment with Stripe.
        """
        try:
            payment_intent = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                stripe.PaymentIntent.create,
                {
                    "amount": payment_data["amount"],
                    "currency": payment_data["currency"],
                    "payment_method": payment_data["payment_method"],
                    "confirm": True
                }
            )
            
            return {
                "payment_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": payment_data["amount"],
                "currency": payment_data["currency"]
            }
        except Exception as e:
            raise ValueError(f"Stripe payment failed: {str(e)}")

    async def process_paypal_payment(self, payment_data: Dict) -> Dict:
        """
        Process payment with PayPal.
        """
        try:
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(payment_data["amount"]),
                        "currency": payment_data["currency"]
                    }
                }]
            })
            
            if not payment.create():
                raise ValueError(payment.error)
            
            return {
                "payment_id": payment.id,
                "status": payment.state,
                "amount": payment_data["amount"],
                "currency": payment_data["currency"]
            }
        except Exception as e:
            raise ValueError(f"PayPal payment failed: {str(e)}")

    async def process_crypto_payment(self, payment_data: Dict) -> Dict:
        """
        Process cryptocurrency payment.
        """
        try:
            # Create transaction
            tx_hash = await self.create_crypto_transaction(payment_data)
            
            # Wait for confirmation
            confirmation = await self.wait_for_crypto_confirmation(tx_hash)
            
            return {
                "payment_id": tx_hash,
                "status": "confirmed" if confirmation else "pending",
                "amount": payment_data["amount"],
                "currency": payment_data["currency"]
            }
        except Exception as e:
            raise ValueError(f"Crypto payment failed: {str(e)}")

    async def create_subscription(self, data: Dict) -> Dict:
        """
        Create new subscription.
        """
        try:
            subscription_id = str(uuid.uuid4())
            
            subscription = {
                "subscription_id": subscription_id,
                "user_id": data["user_id"],
                "plan": data["plan"],
                "status": "active",
                "start_date": datetime.utcnow(),
                "end_date": datetime.utcnow() + timedelta(days=30),
                "auto_renew": data.get("auto_renew", True)
            }
            
            await self.subscriptions.insert_one(subscription)
            
            return {
                "subscription_id": subscription_id,
                "status": "active",
                "details": subscription
            }
        except Exception as e:
            raise ValueError(f"Subscription creation failed: {str(e)}")

    async def calculate_commission(
        self,
        reseller_id: str,
        payment_data: Dict
    ) -> Dict:
        """
        Calculate reseller commission.
        """
        try:
            # Get reseller rate
            rate = await self.get_reseller_rate(reseller_id)
            
            # Calculate commission
            amount = Decimal(payment_data["amount"]) * Decimal(rate)
            
            return {
                "commission_id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "amount": float(amount),
                "rate": rate
            }
        except Exception:
            return {
                "commission_id": str(uuid.uuid4()),
                "reseller_id": reseller_id,
                "amount": 0,
                "rate": 0
            }
