from datetime import datetime
from typing import Optional, List
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import secrets
from passlib.context import CryptContext

from app.core.config import settings
from app.models.auth import UserCreate, UserInDB, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.collection = self.db.users

    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        """
        return pwd_context.verify(plain_password, hashed_password)

    def generate_reset_token(self) -> str:
        """
        Generate a secure reset token.
        """
        return secrets.token_urlsafe(32)

    async def create(self, user_in: UserCreate) -> UserInDB:
        """
        Create a new user.
        """
        # Check if email already exists
        if await self.collection.find_one({"email": user_in.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Verify passwords match
        if user_in.password != user_in.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Create user document
        user = {
            "email": user_in.email,
            "full_name": user_in.full_name,
            "role": user_in.role,
            "is_active": user_in.is_active,
            "hashed_password": self.hash_password(user_in.password),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "two_factor_enabled": False,
            "failed_login_attempts": 0
        }
        
        result = await self.collection.insert_one(user)
        user["id"] = str(result.inserted_id)
        
        return UserInDB(**user)

    async def get(self, user_id: str) -> Optional[UserInDB]:
        """
        Get a user by ID.
        """
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user["id"] = str(user.pop("_id"))
            return UserInDB(**user)
        return None

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """
        Get a user by email.
        """
        user = await self.collection.find_one({"email": email})
        if user:
            user["id"] = str(user.pop("_id"))
            return UserInDB(**user)
        return None

    async def update(self, user_id: str, update_data: dict) -> Optional[UserInDB]:
        """
        Update a user.
        """
        user = await self.collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return None
        
        update_data["updated_at"] = datetime.utcnow()
        
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        updated_user = await self.collection.find_one({"_id": ObjectId(user_id)})
        updated_user["id"] = str(updated_user.pop("_id"))
        return UserInDB(**updated_user)

    async def delete(self, user_id: str) -> bool:
        """
        Delete a user.
        """
        result = await self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[UserInDB]:
        """
        Get all users with pagination.
        """
        users = []
        cursor = self.collection.find().skip(skip).limit(limit)
        async for user in cursor:
            user["id"] = str(user.pop("_id"))
            users.append(UserInDB(**user))
        return users

    async def store_2fa_secret(self, user_id: str, secret: str) -> bool:
        """
        Store 2FA secret for a user.
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "two_factor_secret": secret,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    async def enable_2fa(self, user_id: str) -> bool:
        """
        Enable 2FA for a user.
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "two_factor_enabled": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0

    async def disable_2fa(self, user_id: str) -> bool:
        """
        Disable 2FA for a user.
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "two_factor_enabled": False,
                    "two_factor_secret": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
