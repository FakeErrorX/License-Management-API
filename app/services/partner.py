from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import hashlib
import uuid
import json
import redis

from app.core.config import settings
from app.models.database import Reseller, Affiliate

class PartnerService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.resellers = self.db.resellers
        self.affiliates = self.db.affiliates
        self.commissions = self.db.commissions
        self.redis = redis.Redis.from_url(settings.REDIS_URL)

    async def create_reseller(
        self,
        user_id: str,
        company_name: str,
        commission_rate: float,
        metadata: Dict = None
    ) -> Dict:
        """
        Create a new reseller.
        """
        try:
            # Check if user is already a reseller
            existing = await self.resellers.find_one({"user_id": user_id})
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already a reseller"
                )
            
            reseller = {
                "user_id": user_id,
                "company_name": company_name,
                "commission_rate": commission_rate,
                "total_sales": 0.0,
                "is_active": True,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.resellers.insert_one(reseller)
            reseller["id"] = str(result.inserted_id)
            
            # Cache reseller data
            await self.cache_reseller(reseller)
            
            return reseller
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create reseller: {str(e)}"
            )

    async def create_affiliate(
        self,
        user_id: str,
        commission_rate: float,
        metadata: Dict = None
    ) -> Dict:
        """
        Create a new affiliate.
        """
        try:
            # Check if user is already an affiliate
            existing = await self.affiliates.find_one({"user_id": user_id})
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is already an affiliate"
                )
            
            # Generate unique affiliate code
            affiliate_code = await self.generate_affiliate_code()
            
            affiliate = {
                "user_id": user_id,
                "affiliate_code": affiliate_code,
                "commission_rate": commission_rate,
                "total_earnings": 0.0,
                "is_active": True,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.affiliates.insert_one(affiliate)
            affiliate["id"] = str(result.inserted_id)
            
            # Cache affiliate data
            await self.cache_affiliate(affiliate)
            
            return affiliate
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create affiliate: {str(e)}"
            )

    async def update_reseller(
        self,
        reseller_id: str,
        updates: Dict
    ) -> Dict:
        """
        Update reseller information.
        """
        try:
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.resellers.update_one(
                {"_id": ObjectId(reseller_id)},
                {"$set": updates}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reseller not found"
                )
            
            # Clear cache
            await self.redis.delete(f"reseller:{reseller_id}")
            
            reseller = await self.resellers.find_one({"_id": ObjectId(reseller_id)})
            return {**reseller, "id": str(reseller["_id"])}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update reseller: {str(e)}"
            )

    async def update_affiliate(
        self,
        affiliate_id: str,
        updates: Dict
    ) -> Dict:
        """
        Update affiliate information.
        """
        try:
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.affiliates.update_one(
                {"_id": ObjectId(affiliate_id)},
                {"$set": updates}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Affiliate not found"
                )
            
            # Clear cache
            await self.redis.delete(f"affiliate:{affiliate_id}")
            
            affiliate = await self.affiliates.find_one({"_id": ObjectId(affiliate_id)})
            return {**affiliate, "id": str(affiliate["_id"])}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update affiliate: {str(e)}"
            )

    async def record_reseller_sale(
        self,
        reseller_id: str,
        sale_amount: float,
        customer_id: str
    ) -> Dict:
        """
        Record a sale made by a reseller.
        """
        try:
            reseller = await self.resellers.find_one({"_id": ObjectId(reseller_id)})
            if not reseller:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reseller not found"
                )
            
            commission_amount = sale_amount * reseller["commission_rate"]
            
            # Record commission
            commission = {
                "reseller_id": reseller_id,
                "customer_id": customer_id,
                "sale_amount": sale_amount,
                "commission_amount": commission_amount,
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            
            await self.commissions.insert_one(commission)
            
            # Update reseller total sales
            await self.resellers.update_one(
                {"_id": ObjectId(reseller_id)},
                {
                    "$inc": {"total_sales": sale_amount},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Clear cache
            await self.redis.delete(f"reseller:{reseller_id}")
            
            return {
                "reseller_id": reseller_id,
                "sale_amount": sale_amount,
                "commission_amount": commission_amount
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record sale: {str(e)}"
            )

    async def record_affiliate_referral(
        self,
        affiliate_code: str,
        sale_amount: float,
        customer_id: str
    ) -> Dict:
        """
        Record a referral sale from an affiliate.
        """
        try:
            affiliate = await self.affiliates.find_one({"affiliate_code": affiliate_code})
            if not affiliate:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Affiliate not found"
                )
            
            commission_amount = sale_amount * affiliate["commission_rate"]
            
            # Record commission
            commission = {
                "affiliate_id": str(affiliate["_id"]),
                "customer_id": customer_id,
                "sale_amount": sale_amount,
                "commission_amount": commission_amount,
                "status": "pending",
                "created_at": datetime.utcnow()
            }
            
            await self.commissions.insert_one(commission)
            
            # Update affiliate total earnings
            await self.affiliates.update_one(
                {"_id": affiliate["_id"]},
                {
                    "$inc": {"total_earnings": commission_amount},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            # Clear cache
            await self.redis.delete(f"affiliate:{str(affiliate['_id'])}")
            
            return {
                "affiliate_id": str(affiliate["_id"]),
                "sale_amount": sale_amount,
                "commission_amount": commission_amount
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to record referral: {str(e)}"
            )

    async def get_reseller_analytics(
        self,
        reseller_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Get analytics for a reseller.
        """
        try:
            pipeline = [
                {
                    "$match": {
                        "reseller_id": reseller_id,
                        "created_at": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_sales": {"$sum": "$sale_amount"},
                        "total_commission": {"$sum": "$commission_amount"},
                        "sale_count": {"$sum": 1}
                    }
                }
            ]
            
            result = await self.commissions.aggregate(pipeline).to_list(1)
            
            if not result:
                return {
                    "total_sales": 0,
                    "total_commission": 0,
                    "sale_count": 0
                }
            
            return result[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get analytics: {str(e)}"
            )

    async def get_affiliate_analytics(
        self,
        affiliate_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Get analytics for an affiliate.
        """
        try:
            pipeline = [
                {
                    "$match": {
                        "affiliate_id": affiliate_id,
                        "created_at": {
                            "$gte": start_date,
                            "$lte": end_date
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_sales": {"$sum": "$sale_amount"},
                        "total_commission": {"$sum": "$commission_amount"},
                        "referral_count": {"$sum": 1}
                    }
                }
            ]
            
            result = await self.commissions.aggregate(pipeline).to_list(1)
            
            if not result:
                return {
                    "total_sales": 0,
                    "total_commission": 0,
                    "referral_count": 0
                }
            
            return result[0]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get analytics: {str(e)}"
            )

    async def generate_affiliate_code(self) -> str:
        """
        Generate a unique affiliate code.
        """
        while True:
            code = str(uuid.uuid4())[:8].upper()
            existing = await self.affiliates.find_one({"affiliate_code": code})
            if not existing:
                return code

    async def cache_reseller(self, reseller: Dict) -> None:
        """
        Cache reseller data.
        """
        try:
            await self.redis.setex(
                f"reseller:{str(reseller['_id'])}",
                300,  # 5 minutes cache
                json.dumps(reseller)
            )
        except Exception:
            pass  # Fail silently on cache errors

    async def cache_affiliate(self, affiliate: Dict) -> None:
        """
        Cache affiliate data.
        """
        try:
            await self.redis.setex(
                f"affiliate:{str(affiliate['_id'])}",
                300,  # 5 minutes cache
                json.dumps(affiliate)
            )
        except Exception:
            pass  # Fail silently on cache errors

    async def get_commission_payouts(
        self,
        partner_id: str,
        partner_type: str,
        status: str = "pending"
    ) -> List[Dict]:
        """
        Get commission payouts for a partner.
        """
        try:
            query = {
                f"{partner_type}_id": partner_id,
                "status": status
            }
            
            payouts = await self.commissions.find(query).to_list(None)
            return [{**payout, "id": str(payout["_id"])} for payout in payouts]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get payouts: {str(e)}"
            )

    async def process_commission_payout(
        self,
        commission_id: str,
        payout_details: Dict
    ) -> Dict:
        """
        Process a commission payout.
        """
        try:
            result = await self.commissions.update_one(
                {"_id": ObjectId(commission_id)},
                {
                    "$set": {
                        "status": "paid",
                        "payout_details": payout_details,
                        "paid_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Commission not found"
                )
            
            commission = await self.commissions.find_one(
                {"_id": ObjectId(commission_id)}
            )
            return {**commission, "id": str(commission["_id"])}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process payout: {str(e)}"
            )
