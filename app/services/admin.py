from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import json
from bson import ObjectId

from app.core.config import settings
from app.models.auth import UserInDB, UserRole

class AdminService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.users = self.db.users
        self.licenses = self.db.licenses
        self.audit_logs = self.db.audit_logs
        self.api_keys = self.db.api_keys
        self.resellers = self.db.resellers
        self.cache = {}  # Simple in-memory cache

    async def get_dashboard_metrics(self) -> Dict:
        """
        Get admin dashboard overview metrics.
        """
        try:
            # Get user metrics
            total_users = await self.users.count_documents({})
            active_users = await self.users.count_documents({"is_active": True})
            
            # Get license metrics
            total_licenses = await self.licenses.count_documents({})
            active_licenses = await self.licenses.count_documents({"is_active": True})
            
            # Get revenue metrics
            revenue_stats = await self._calculate_revenue_metrics()
            
            # Get system metrics
            system_health = await self.get_system_health()
            
            return {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "inactive": total_users - active_users
                },
                "licenses": {
                    "total": total_licenses,
                    "active": active_licenses,
                    "inactive": total_licenses - active_licenses
                },
                "revenue": revenue_stats,
                "system_health": system_health
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        Get all users with pagination.
        """
        try:
            users = await self.users.find().skip(skip).limit(limit).to_list(None)
            return [
                {
                    **user,
                    "id": str(user["_id"]),
                    "created_at": user.get("created_at", datetime.utcnow())
                }
                for user in users
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def update_user_role(self, user_id: str, role: UserRole) -> Dict:
        """
        Update user role.
        """
        try:
            result = await self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"role": role.value}}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Log the role change
            await self._log_audit_event(
                "user_role_update",
                {"user_id": user_id, "new_role": role.value}
            )
            
            return {"status": "success", "message": f"User role updated to {role.value}"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def get_all_licenses(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        Get all licenses with pagination.
        """
        try:
            licenses = await self.licenses.find().skip(skip).limit(limit).to_list(None)
            return [
                {
                    **license,
                    "id": str(license["_id"]),
                    "created_at": license.get("created_at", datetime.utcnow())
                }
                for license in licenses
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def bulk_license_action(self, action: str, license_ids: List[str]) -> Dict:
        """
        Perform bulk action on licenses.
        """
        try:
            if action not in ["activate", "deactivate", "delete"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid action"
                )
            
            license_object_ids = [ObjectId(lid) for lid in license_ids]
            
            if action == "delete":
                result = await self.licenses.delete_many({"_id": {"$in": license_object_ids}})
                modified = result.deleted_count
            else:
                is_active = action == "activate"
                result = await self.licenses.update_many(
                    {"_id": {"$in": license_object_ids}},
                    {"$set": {"is_active": is_active}}
                )
                modified = result.modified_count
            
            # Log the bulk action
            await self._log_audit_event(
                f"bulk_license_{action}",
                {"license_ids": license_ids, "modified_count": modified}
            )
            
            return {
                "status": "success",
                "modified_count": modified
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def get_audit_logs(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """
        Get system audit logs.
        """
        try:
            logs = await self.audit_logs.find().sort(
                "timestamp", -1
            ).skip(skip).limit(limit).to_list(None)
            
            return [
                {
                    **log,
                    "id": str(log["_id"]),
                    "timestamp": log.get("timestamp", datetime.utcnow())
                }
                for log in logs
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def get_system_health(self) -> Dict:
        """
        Get system health metrics.
        """
        try:
            # Database health check
            db_status = await self._check_database_health()
            
            # Cache health check
            cache_status = self._check_cache_health()
            
            # API performance metrics
            api_metrics = await self._get_api_metrics()
            
            return {
                "database": db_status,
                "cache": cache_status,
                "api": api_metrics,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def toggle_maintenance_mode(self, enabled: bool) -> Dict:
        """
        Toggle system maintenance mode.
        """
        try:
            # Update system settings
            await self.db.settings.update_one(
                {"key": "maintenance_mode"},
                {"$set": {"value": enabled}},
                upsert=True
            )
            
            # Log the maintenance mode change
            await self._log_audit_event(
                "maintenance_mode_update",
                {"enabled": enabled}
            )
            
            return {
                "status": "success",
                "maintenance_mode": enabled
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def clear_cache(self, cache_type: str) -> Dict:
        """
        Clear system cache.
        """
        try:
            if cache_type == "all":
                self.cache.clear()
            elif cache_type in self.cache:
                del self.cache[cache_type]
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid cache type: {cache_type}"
                )
            
            # Log cache clear
            await self._log_audit_event(
                "cache_clear",
                {"cache_type": cache_type}
            )
            
            return {"status": "success", "message": f"Cache {cache_type} cleared"}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def get_security_settings(self) -> Dict:
        """
        Get security settings.
        """
        try:
            settings = await self.db.settings.find_one({"key": "security"})
            return settings.get("value", {}) if settings else {}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def update_security_settings(self, settings: Dict) -> Dict:
        """
        Update security settings.
        """
        try:
            await self.db.settings.update_one(
                {"key": "security"},
                {"$set": {"value": settings}},
                upsert=True
            )
            
            # Log security settings update
            await self._log_audit_event(
                "security_settings_update",
                {"settings": settings}
            )
            
            return {"status": "success", "settings": settings}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def generate_report(
        self,
        report_type: str,
        start_date: str,
        end_date: str
    ) -> Dict:
        """
        Generate administrative reports.
        """
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            if report_type == "user_activity":
                return await self._generate_user_activity_report(start, end)
            elif report_type == "license_usage":
                return await self._generate_license_usage_report(start, end)
            elif report_type == "revenue":
                return await self._generate_revenue_report(start, end)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid report type: {report_type}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def send_notification(self, notification: Dict) -> Dict:
        """
        Send administrative notifications.
        """
        try:
            # Add notification to queue
            notification["timestamp"] = datetime.utcnow()
            await self.db.notifications.insert_one(notification)
            
            # Log notification
            await self._log_audit_event(
                "notification_sent",
                {"notification": notification}
            )
            
            return {"status": "success", "notification": notification}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def get_api_keys(self) -> List[Dict]:
        """
        Get all API keys.
        """
        try:
            api_keys = await self.api_keys.find().to_list(None)
            return [
                {
                    **key,
                    "id": str(key["_id"]),
                    "created_at": key.get("created_at", datetime.utcnow())
                }
                for key in api_keys
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def rotate_api_keys(self, key_ids: List[str]) -> Dict:
        """
        Rotate specified API keys.
        """
        try:
            key_object_ids = [ObjectId(kid) for kid in key_ids]
            
            # Generate new API keys
            for key_id in key_object_ids:
                new_key = self._generate_api_key()
                await self.api_keys.update_one(
                    {"_id": key_id},
                    {
                        "$set": {
                            "key": new_key,
                            "rotated_at": datetime.utcnow()
                        }
                    }
                )
            
            # Log key rotation
            await self._log_audit_event(
                "api_key_rotation",
                {"key_ids": key_ids}
            )
            
            return {"status": "success", "rotated_count": len(key_ids)}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def get_resellers(self) -> List[Dict]:
        """
        Get all resellers.
        """
        try:
            resellers = await self.resellers.find().to_list(None)
            return [
                {
                    **reseller,
                    "id": str(reseller["_id"]),
                    "created_at": reseller.get("created_at", datetime.utcnow())
                }
                for reseller in resellers
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def update_reseller_commission(
        self,
        reseller_id: str,
        commission_rate: float
    ) -> Dict:
        """
        Update reseller commission rate.
        """
        try:
            if not 0 <= commission_rate <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Commission rate must be between 0 and 1"
                )
            
            result = await self.resellers.update_one(
                {"_id": ObjectId(reseller_id)},
                {"$set": {"commission_rate": commission_rate}}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reseller not found"
                )
            
            # Log commission update
            await self._log_audit_event(
                "reseller_commission_update",
                {
                    "reseller_id": reseller_id,
                    "new_rate": commission_rate
                }
            )
            
            return {
                "status": "success",
                "reseller_id": reseller_id,
                "commission_rate": commission_rate
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

    async def _log_audit_event(self, event_type: str, data: Dict) -> None:
        """
        Log an audit event.
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        
        await self.audit_logs.insert_one(event)

    async def _check_database_health(self) -> Dict:
        """
        Check database health.
        """
        try:
            # Ping database
            await self.db.command("ping")
            return {"status": "healthy", "latency": "0ms"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def _check_cache_health(self) -> Dict:
        """
        Check cache health.
        """
        return {
            "status": "healthy",
            "size": len(self.cache),
            "memory_usage": "0MB"  # Placeholder
        }

    async def _get_api_metrics(self) -> Dict:
        """
        Get API performance metrics.
        """
        # This would typically integrate with a monitoring service
        return {
            "requests_per_second": 0,
            "average_latency": "0ms",
            "error_rate": "0%"
        }

    async def _calculate_revenue_metrics(self) -> Dict:
        """
        Calculate revenue metrics.
        """
        # This would typically calculate actual revenue from payment records
        return {
            "total": 0,
            "monthly": 0,
            "growth": "0%"
        }

    def _generate_api_key(self) -> str:
        """
        Generate a new API key.
        """
        # Implementation would generate a secure API key
        return "new_api_key"

    async def _generate_user_activity_report(
        self,
        start: datetime,
        end: datetime
    ) -> Dict:
        """
        Generate user activity report.
        """
        # Implementation would generate actual user activity report
        return {"type": "user_activity", "data": []}

    async def _generate_license_usage_report(
        self,
        start: datetime,
        end: datetime
    ) -> Dict:
        """
        Generate license usage report.
        """
        # Implementation would generate actual license usage report
        return {"type": "license_usage", "data": []}

    async def _generate_revenue_report(
        self,
        start: datetime,
        end: datetime
    ) -> Dict:
        """
        Generate revenue report.
        """
        # Implementation would generate actual revenue report
        return {"type": "revenue", "data": []}
