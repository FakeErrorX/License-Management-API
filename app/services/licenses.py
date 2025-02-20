from datetime import datetime, timedelta
from typing import Optional, List, Dict
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import secrets
import string
import hashlib
from app.core.config import settings
from app.models.license import (
    License,
    LicenseCreate,
    LicenseUpdate,
    LicenseValidation,
    LicenseStatus,
    BulkLicenseCreate,
    LicenseAnalytics
)
from app.models.auth import UserInDB

class LicenseService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.collection = self.db.licenses
        self.usage_collection = self.db.license_usage

    def generate_license_key(self) -> str:
        """
        Generate a unique license key.
        """
        # Generate a random string of 16 characters
        chars = string.ascii_uppercase + string.digits
        random_str = ''.join(secrets.choice(chars) for _ in range(16))
        
        # Format into groups of 4
        return '-'.join(random_str[i:i+4] for i in range(0, 16, 4))

    def hash_license_key(self, key: str) -> str:
        """
        Create a secure hash of the license key.
        """
        return hashlib.sha256(key.encode()).hexdigest()

    async def create(self, license_in: LicenseCreate, current_user: UserInDB) -> License:
        """
        Create a new license.
        """
        # Check if user has permission to create licenses
        if not current_user.is_active or (
            current_user.role not in ["admin", "reseller"] and
            str(current_user.id) != license_in.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Generate unique license key
        while True:
            license_key = self.generate_license_key()
            existing = await self.collection.find_one({"key": license_key})
            if not existing:
                break
        
        # Calculate expiration date
        expiration_date = None
        if license_in.expiration_days:
            expiration_date = datetime.utcnow() + timedelta(days=license_in.expiration_days)
        
        # Create license document
        license_doc = {
            "key": license_key,
            "key_hash": self.hash_license_key(license_key),
            "type": license_in.type,
            "user_id": license_in.user_id,
            "features": [feature.dict() for feature in license_in.features],
            "max_activations": license_in.max_activations,
            "current_activations": 0,
            "expiration_date": expiration_date,
            "status": LicenseStatus.ACTIVE,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "ip_restriction": license_in.ip_restriction,
            "domain_restriction": license_in.domain_restriction,
            "metadata": license_in.metadata or {},
            "activation_history": []
        }
        
        result = await self.collection.insert_one(license_doc)
        license_doc["id"] = str(result.inserted_id)
        
        return License(**license_doc)

    async def bulk_create(
        self,
        bulk_license: BulkLicenseCreate,
        current_user: UserInDB
    ) -> List[License]:
        """
        Create multiple licenses in bulk.
        """
        if not current_user.is_active or current_user.role not in ["admin", "reseller"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        licenses = []
        for _ in range(bulk_license.count):
            license = await self.create(bulk_license.license_data, current_user)
            licenses.append(license)
        
        return licenses

    async def validate(self, license_key: str) -> LicenseValidation:
        """
        Validate a license key.
        """
        license = await self.collection.find_one({"key": license_key})
        if not license:
            return LicenseValidation(
                is_valid=False,
                license_key=license_key,
                status=LicenseStatus.REVOKED,
                features=[],
                message="Invalid license key"
            )
        
        # Check expiration
        if license.get("expiration_date") and license["expiration_date"] < datetime.utcnow():
            await self.collection.update_one(
                {"_id": license["_id"]},
                {"$set": {"status": LicenseStatus.EXPIRED}}
            )
            return LicenseValidation(
                is_valid=False,
                license_key=license_key,
                status=LicenseStatus.EXPIRED,
                features=license["features"],
                expiration_date=license["expiration_date"],
                message="License has expired"
            )
        
        # Update last check time
        await self.collection.update_one(
            {"_id": license["_id"]},
            {"$set": {"last_check": datetime.utcnow()}}
        )
        
        return LicenseValidation(
            is_valid=True,
            license_key=license_key,
            status=license["status"],
            features=license["features"],
            expiration_date=license.get("expiration_date"),
            message="License is valid"
        )

    async def update(
        self,
        license_id: str,
        license_in: LicenseUpdate,
        current_user: UserInDB
    ) -> Optional[License]:
        """
        Update a license.
        """
        license = await self.collection.find_one({"_id": ObjectId(license_id)})
        if not license:
            return None
        
        # Check permissions
        if not current_user.is_active or (
            current_user.role not in ["admin"] and
            str(current_user.id) != license["user_id"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        update_data = license_in.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        await self.collection.update_one(
            {"_id": ObjectId(license_id)},
            {"$set": update_data}
        )
        
        updated_license = await self.collection.find_one({"_id": ObjectId(license_id)})
        updated_license["id"] = str(updated_license.pop("_id"))
        return License(**updated_license)

    async def revoke(self, license_id: str, current_user: UserInDB) -> bool:
        """
        Revoke a license.
        """
        license = await self.collection.find_one({"_id": ObjectId(license_id)})
        if not license:
            return False
        
        if not current_user.is_active or (
            current_user.role not in ["admin"] and
            str(current_user.id) != license["user_id"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        await self.collection.update_one(
            {"_id": ObjectId(license_id)},
            {
                "$set": {
                    "status": LicenseStatus.REVOKED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return True

    async def get_analytics(
        self,
        license_id: str,
        current_user: UserInDB
    ) -> Optional[LicenseAnalytics]:
        """
        Get analytics for a license.
        """
        license = await self.collection.find_one({"_id": ObjectId(license_id)})
        if not license:
            return None
        
        if not current_user.is_active or (
            current_user.role not in ["admin"] and
            str(current_user.id) != license["user_id"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        # Get usage history
        usage_history = await self.usage_collection.find(
            {"license_id": license_id}
        ).sort("timestamp", -1).limit(100).to_list(None)
        
        # Calculate feature usage
        feature_usage = {}
        for usage in usage_history:
            feature = usage["feature_name"]
            feature_usage[feature] = feature_usage.get(feature, 0) + usage["usage_count"]
        
        return LicenseAnalytics(
            total_activations=license["current_activations"],
            active_devices=license["activation_history"],
            usage_history=usage_history,
            feature_usage=feature_usage,
            last_validation=license.get("last_check")
        )

    async def transfer(
        self,
        license_id: str,
        new_user_id: str,
        current_user: UserInDB
    ) -> bool:
        """
        Transfer a license to another user.
        """
        license = await self.collection.find_one({"_id": ObjectId(license_id)})
        if not license:
            return False
        
        if not current_user.is_active or (
            current_user.role not in ["admin"] and
            str(current_user.id) != license["user_id"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        await self.collection.update_one(
            {"_id": ObjectId(license_id)},
            {
                "$set": {
                    "user_id": new_user_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return True
