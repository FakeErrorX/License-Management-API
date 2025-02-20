from typing import Dict, List, Optional
from fastapi import HTTPException
from datetime import datetime, timedelta
import uuid
import jwt
from app.core.config import settings
from app.models.user import UserInDB

class AdvancedLicensingService:
    def __init__(self, db):
        self.db = db
        self.licenses = self.db.licenses
        self.license_usage = self.db.license_usage
        self.features = self.db.features

    async def create_user_based_license(
        self,
        user: UserInDB,
        features: List[str],
        max_users: int,
        duration_days: int
    ) -> Dict:
        """Create a user-based license with specific features."""
        try:
            license_id = str(uuid.uuid4())
            expiry_date = datetime.now() + timedelta(days=duration_days)

            license_data = {
                "license_id": license_id,
                "user_id": str(user.id),
                "type": "user_based",
                "features": features,
                "max_users": max_users,
                "current_users": 1,
                "created_at": datetime.now(),
                "expires_at": expiry_date,
                "status": "active"
            }

            await self.licenses.insert_one(license_data)

            return {
                "license_id": license_id,
                "features": features,
                "max_users": max_users,
                "expires_at": expiry_date.isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create user-based license: {str(e)}"
            )

    async def create_project_based_license(
        self,
        user: UserInDB,
        project_id: str,
        features: List[str],
        max_projects: int,
        duration_days: int
    ) -> Dict:
        """Create a project-based license."""
        try:
            license_id = str(uuid.uuid4())
            expiry_date = datetime.now() + timedelta(days=duration_days)

            license_data = {
                "license_id": license_id,
                "user_id": str(user.id),
                "project_id": project_id,
                "type": "project_based",
                "features": features,
                "max_projects": max_projects,
                "current_projects": 1,
                "created_at": datetime.now(),
                "expires_at": expiry_date,
                "status": "active"
            }

            await self.licenses.insert_one(license_data)

            return {
                "license_id": license_id,
                "project_id": project_id,
                "features": features,
                "max_projects": max_projects,
                "expires_at": expiry_date.isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create project-based license: {str(e)}"
            )

    async def create_time_limited_feature(
        self,
        user: UserInDB,
        feature_id: str,
        duration_hours: int
    ) -> Dict:
        """Create a time-limited feature access."""
        try:
            access_id = str(uuid.uuid4())
            expiry_date = datetime.now() + timedelta(hours=duration_hours)

            access_data = {
                "access_id": access_id,
                "user_id": str(user.id),
                "feature_id": feature_id,
                "type": "time_limited",
                "created_at": datetime.now(),
                "expires_at": expiry_date,
                "status": "active"
            }

            await self.features.insert_one(access_data)

            return {
                "access_id": access_id,
                "feature_id": feature_id,
                "expires_at": expiry_date.isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create time-limited feature: {str(e)}"
            )

    async def create_offline_license(
        self,
        user: UserInDB,
        features: List[str],
        duration_days: int,
        device_id: str
    ) -> Dict:
        """Create an offline license with device binding."""
        try:
            license_id = str(uuid.uuid4())
            expiry_date = datetime.now() + timedelta(days=duration_days)

            # Create license token
            license_token = jwt.encode(
                {
                    "license_id": license_id,
                    "user_id": str(user.id),
                    "device_id": device_id,
                    "features": features,
                    "created_at": datetime.now().isoformat(),
                    "expires_at": expiry_date.isoformat()
                },
                settings.JWT_SECRET,
                algorithm="HS256"
            )

            license_data = {
                "license_id": license_id,
                "user_id": str(user.id),
                "device_id": device_id,
                "type": "offline",
                "features": features,
                "created_at": datetime.now(),
                "expires_at": expiry_date,
                "status": "active",
                "license_token": license_token
            }

            await self.licenses.insert_one(license_data)

            return {
                "license_id": license_id,
                "license_token": license_token,
                "features": features,
                "device_id": device_id,
                "expires_at": expiry_date.isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create offline license: {str(e)}"
            )

    async def verify_license(
        self,
        license_id: str,
        feature: str = None
    ) -> Dict:
        """Verify a license and optionally check feature access."""
        try:
            license_data = await self.licenses.find_one({"license_id": license_id})
            if not license_data:
                raise HTTPException(
                    status_code=404,
                    detail="License not found"
                )

            # Check expiration
            if datetime.now() > license_data["expires_at"]:
                await self.licenses.update_one(
                    {"license_id": license_id},
                    {"$set": {"status": "expired"}}
                )
                raise HTTPException(
                    status_code=403,
                    detail="License has expired"
                )

            # Check feature access if specified
            if feature and feature not in license_data["features"]:
                raise HTTPException(
                    status_code=403,
                    detail=f"License does not include access to feature: {feature}"
                )

            # Log license usage
            await self.license_usage.insert_one({
                "license_id": license_id,
                "feature": feature,
                "timestamp": datetime.now()
            })

            return {
                "valid": True,
                "type": license_data["type"],
                "features": license_data["features"],
                "expires_at": license_data["expires_at"].isoformat()
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500,
                detail=f"License verification failed: {str(e)}"
            )

    async def transfer_license(
        self,
        license_id: str,
        from_user_id: str,
        to_user_id: str
    ) -> Dict:
        """Transfer a license from one user to another."""
        try:
            # Verify license exists and belongs to from_user
            license_data = await self.licenses.find_one({
                "license_id": license_id,
                "user_id": from_user_id
            })

            if not license_data:
                raise HTTPException(
                    status_code=404,
                    detail="License not found or does not belong to the user"
                )

            # Update license ownership
            await self.licenses.update_one(
                {"license_id": license_id},
                {
                    "$set": {
                        "user_id": to_user_id,
                        "transfer_date": datetime.now()
                    }
                }
            )

            return {
                "license_id": license_id,
                "new_owner_id": to_user_id,
                "transfer_date": datetime.now().isoformat()
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500,
                detail=f"License transfer failed: {str(e)}"
            )
