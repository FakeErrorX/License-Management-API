from datetime import datetime
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import stripe
import json
import httpx
from bson import ObjectId

from app.core.config import settings
from app.models.auth import UserInDB
from app.models.payment import (
    PaymentCreate,
    PaymentUpdate,
    SubscriptionCreate,
    PaymentMethod,
    Invoice,
    PaymentProvider,
    PaymentStatus
)

class PaymentService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.payments = self.db.payments
        self.subscriptions = self.db.subscriptions
        self.payment_methods = self.db.payment_methods
        self.invoices = self.db.invoices
        
        # Initialize payment providers
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
        self.bkash_service = BkashService()  # Initialize bKash service

    async def create_payment(self, user: UserInDB, payment: PaymentCreate) -> Dict:
        """
        Create a new payment using specified payment method.
        """
        try:
            if payment.provider == "stripe":
                return await self._create_stripe_payment(user, payment)
            elif payment.provider == "paypal":
                return await self._create_paypal_payment(user, payment)
            elif payment.provider == "crypto":
                return await self._create_crypto_payment(user, payment)
            elif payment.provider == PaymentProvider.BKASH:
                return await self._create_bkash_payment(user, payment)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported payment provider: {payment.provider}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def _create_stripe_payment(self, user: UserInDB, payment: PaymentCreate) -> Dict:
        """
        Create a Stripe payment.
        """
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=payment.amount,
                currency=payment.currency,
                customer=user.stripe_customer_id,
                payment_method=payment.payment_method_id,
                confirm=True,
                return_url=payment.return_url
            )
            
            # Store payment record
            payment_record = {
                "user_id": str(user.id),
                "provider": "stripe",
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment_intent.status,
                "payment_intent_id": payment_intent.id,
                "created_at": datetime.utcnow()
            }
            
            await self.payments.insert_one(payment_record)
            
            return {
                "id": payment_intent.id,
                "status": payment_intent.status,
                "client_secret": payment_intent.client_secret
            }
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def create_subscription(
        self,
        user: UserInDB,
        subscription: SubscriptionCreate
    ) -> Dict:
        """
        Create a new subscription.
        """
        try:
            if subscription.provider == "stripe":
                stripe_subscription = stripe.Subscription.create(
                    customer=user.stripe_customer_id,
                    items=[{"price": subscription.price_id}],
                    payment_behavior="default_incomplete",
                    expand=["latest_invoice.payment_intent"]
                )
                
                # Store subscription record
                subscription_record = {
                    "user_id": str(user.id),
                    "provider": "stripe",
                    "subscription_id": stripe_subscription.id,
                    "status": stripe_subscription.status,
                    "current_period_end": datetime.fromtimestamp(
                        stripe_subscription.current_period_end
                    ),
                    "created_at": datetime.utcnow()
                }
                
                await self.subscriptions.insert_one(subscription_record)
                
                return {
                    "subscription_id": stripe_subscription.id,
                    "status": stripe_subscription.status,
                    "client_secret": stripe_subscription.latest_invoice.payment_intent.client_secret
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported subscription provider: {subscription.provider}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def process_crypto_payment(self, user: UserInDB, payment: PaymentCreate) -> Dict:
        """
        Process a cryptocurrency payment.
        """
        try:
            # Implementation would integrate with crypto payment processor
            payment_record = {
                "user_id": str(user.id),
                "provider": "crypto",
                "amount": payment.amount,
                "currency": payment.currency,
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            
            result = await self.payments.insert_one(payment_record)
            
            return {
                "payment_id": str(result.inserted_id),
                "status": "pending",
                "wallet_address": "your_crypto_wallet_address"  # Would be dynamic in production
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def get_payment_methods(self, user: UserInDB) -> List[Dict]:
        """
        Get all payment methods for a user.
        """
        payment_methods = await self.payment_methods.find(
            {"user_id": str(user.id)}
        ).to_list(None)
        
        return payment_methods

    async def add_payment_method(
        self,
        user: UserInDB,
        payment_method: PaymentMethod
    ) -> Dict:
        """
        Add a new payment method.
        """
        try:
            if payment_method.type == "card":
                # Create payment method in Stripe
                stripe_pm = stripe.PaymentMethod.attach(
                    payment_method.token,
                    customer=user.stripe_customer_id
                )
                
                # Store payment method record
                pm_record = {
                    "user_id": str(user.id),
                    "provider": "stripe",
                    "type": payment_method.type,
                    "last4": stripe_pm.card.last4,
                    "brand": stripe_pm.card.brand,
                    "exp_month": stripe_pm.card.exp_month,
                    "exp_year": stripe_pm.card.exp_year,
                    "payment_method_id": stripe_pm.id,
                    "created_at": datetime.utcnow()
                }
                
                await self.payment_methods.insert_one(pm_record)
                
                return pm_record
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported payment method type: {payment_method.type}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def get_invoices(self, user: UserInDB) -> List[Invoice]:
        """
        Get all invoices for a user.
        """
        invoices = await self.invoices.find(
            {"user_id": str(user.id)}
        ).sort("created_at", -1).to_list(None)
        
        return [Invoice(**invoice) for invoice in invoices]

    async def pay_invoice(
        self,
        user: UserInDB,
        invoice_id: str,
        payment_method_id: str
    ) -> Dict:
        """
        Pay a specific invoice.
        """
        invoice = await self.invoices.find_one({"_id": ObjectId(invoice_id)})
        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        
        try:
            payment = await self.create_payment(
                user,
                PaymentCreate(
                    amount=invoice["amount"],
                    currency=invoice["currency"],
                    payment_method_id=payment_method_id,
                    provider="stripe"
                )
            )
            
            # Update invoice status
            await self.invoices.update_one(
                {"_id": ObjectId(invoice_id)},
                {
                    "$set": {
                        "status": "paid",
                        "payment_id": payment["id"],
                        "paid_at": datetime.utcnow()
                    }
                }
            )
            
            return {"status": "paid", "payment": payment}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def process_refund(self, user: UserInDB, payment_id: str) -> Dict:
        """
        Process a refund for a payment.
        """
        payment = await self.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        try:
            if payment["provider"] == "stripe":
                refund = stripe.Refund.create(
                    payment_intent=payment["payment_intent_id"]
                )
                
                await self.payments.update_one(
                    {"_id": ObjectId(payment_id)},
                    {
                        "$set": {
                            "status": "refunded",
                            "refund_id": refund.id,
                            "refunded_at": datetime.utcnow()
                        }
                    }
                )
                
                return {"status": "refunded", "refund_id": refund.id}
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Refunds not supported for provider: {payment['provider']}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def get_pricing_tiers(self) -> List[Dict]:
        """
        Get available pricing tiers.
        """
        # This would typically fetch from a database
        return [
            {
                "id": "basic",
                "name": "Basic",
                "price": 10,
                "currency": "USD",
                "features": ["Feature 1", "Feature 2"]
            },
            {
                "id": "pro",
                "name": "Professional",
                "price": 25,
                "currency": "USD",
                "features": ["Feature 1", "Feature 2", "Feature 3"]
            }
        ]

    async def register_affiliate(self, user: UserInDB) -> Dict:
        """
        Register user as an affiliate.
        """
        # Check if already registered
        existing = await self.db.affiliates.find_one({"user_id": str(user.id)})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already registered as affiliate"
            )
        
        affiliate_record = {
            "user_id": str(user.id),
            "affiliate_id": f"AFF{str(ObjectId())}",
            "commission_rate": 0.1,  # 10% default commission
            "total_earnings": 0,
            "created_at": datetime.utcnow()
        }
        
        await self.db.affiliates.insert_one(affiliate_record)
        
        return {
            "affiliate_id": affiliate_record["affiliate_id"],
            "commission_rate": affiliate_record["commission_rate"]
        }

    async def get_affiliate_earnings(self, user: UserInDB) -> Dict:
        """
        Get affiliate earnings and statistics.
        """
        affiliate = await self.db.affiliates.find_one({"user_id": str(user.id)})
        if not affiliate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not registered as affiliate"
            )
        
        # Get referral statistics
        referrals = await self.db.referrals.find(
            {"affiliate_id": affiliate["affiliate_id"]}
        ).to_list(None)
        
        return {
            "total_earnings": affiliate["total_earnings"],
            "commission_rate": affiliate["commission_rate"],
            "total_referrals": len(referrals),
            "recent_earnings": [
                {
                    "amount": ref["commission_amount"],
                    "date": ref["created_at"]
                }
                for ref in referrals[-5:]  # Last 5 referrals
            ]
        }

    async def _create_bkash_payment(self, user: UserInDB, payment: PaymentCreate) -> Dict:
        """Create a bKash payment."""
        try:
            # Generate a unique invoice number
            invoice_number = f"INV-{user.id}-{int(datetime.now().timestamp())}"
            
            # Create bKash payment request
            bkash_payment = await self.bkash_service.create_payment(
                amount=payment.amount,
                invoice_number=invoice_number
            )

            # Store payment record
            payment_record = {
                "user_id": user.id,
                "provider": "bkash",
                "amount": payment.amount,
                "currency": "BDT",
                "status": PaymentStatus.PENDING,
                "payment_id": bkash_payment["paymentID"],
                "merchant_invoice_number": invoice_number,
                "metadata": payment.metadata
            }

            await self.payments.insert_one(payment_record)

            return {
                "payment_id": bkash_payment["paymentID"],
                "status": PaymentStatus.PENDING,
                "bkash_url": bkash_payment["bkashURL"]
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def execute_bkash_payment(self, payment_id: str) -> Dict:
        """Execute a bKash payment after user confirmation."""
        try:
            # Execute the payment
            result = await self.bkash_service.execute_payment(payment_id)
            
            # Update payment status in database
            await self.payments.update_one(
                {"payment_id": payment_id},
                {
                    "$set": {
                        "status": PaymentStatus.COMPLETED,
                        "transaction_id": result["trxID"],
                        "payment_execute_time": result["paymentExecuteTime"]
                    }
                }
            )

            return result

        except Exception as e:
            # Update payment status to failed
            await self.payments.update_one(
                {"payment_id": payment_id},
                {"$set": {"status": PaymentStatus.FAILED}}
            )
            raise HTTPException(status_code=400, detail=str(e))

    async def query_bkash_payment(self, payment_id: str) -> Dict:
        """Query the status of a bKash payment."""
        return await self.bkash_service.query_payment(payment_id)

    async def refund_bkash_payment(
        self, 
        payment_id: str, 
        amount: float,
        reason: str = "Customer requested refund"
    ) -> Dict:
        """Refund a bKash payment."""
        try:
            result = await self.bkash_service.refund_payment(
                payment_id=payment_id,
                amount=amount,
                reason=reason
            )

            # Update payment status in database
            await self.payments.update_one(
                {"payment_id": payment_id},
                {"$set": {"status": PaymentStatus.REFUNDED}}
            )

            return result

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
