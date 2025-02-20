from datetime import datetime, timedelta
from typing import Optional, Any
from fastapi import HTTPException, status, Request
from motor.motor_asyncio import AsyncIOMotorClient
import jwt
from bson import ObjectId

from app.core.config import settings
from app.models.auth import UserInDB, UserCreate, UserRole
from app.services.users import UserService

class AuthService:
    def __init__(self):
        self.user_service = UserService()
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.collection = self.db.users

    async def authenticate(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate a user with email and password.
        """
        user = await self.user_service.get_by_email(email)
        if not user:
            return None
        
        # Check failed login attempts
        if user.failed_login_attempts >= 5:
            last_attempt = user.last_login or datetime.utcnow()
            if (datetime.utcnow() - last_attempt) < timedelta(minutes=15):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Account temporarily locked. Try again later."
                )
            # Reset failed attempts after lockout period
            await self.collection.update_one(
                {"_id": ObjectId(user.id)},
                {"$set": {"failed_login_attempts": 0}}
            )
        
        if not self.user_service.verify_password(password, user.hashed_password):
            # Increment failed attempts
            await self.collection.update_one(
                {"_id": ObjectId(user.id)},
                {
                    "$inc": {"failed_login_attempts": 1},
                    "$set": {"last_login": datetime.utcnow()}
                }
            )
            return None
        
        # Reset failed attempts on successful login
        await self.collection.update_one(
            {"_id": ObjectId(user.id)},
            {
                "$set": {
                    "failed_login_attempts": 0,
                    "last_login": datetime.utcnow()
                }
            }
        )
        return user

    async def get_current_user(self, token: str) -> UserInDB:
        """
        Get current user from JWT token.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.ALGORITHM]
            )
            user_id = payload.get("sub")
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        user = await self.user_service.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def oauth_login(self, provider: str, request: Request) -> Any:
        """
        Handle OAuth2 login for various providers.
        """
        if provider not in ["google", "github", "microsoft"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        # Implementation for each provider would go here
        # This is a placeholder for the OAuth2 flow
        return {"message": f"OAuth2 login with {provider} not implemented yet"}

    async def logout(self, token: str) -> bool:
        """
        Logout user and invalidate token.
        """
        # Add token to blacklist in Redis
        # Implementation would go here
        return True

    async def create_admin_user(self, user_in: UserCreate) -> UserInDB:
        """
        Create an admin user.
        """
        user_in.role = UserRole.ADMIN
        return await self.user_service.create(user_in)

    async def reset_password(self, email: str) -> bool:
        """
        Initiate password reset process.
        """
        user = await self.user_service.get_by_email(email)
        if not user:
            return False
        
        # Generate reset token
        reset_token = self.user_service.generate_reset_token()
        expires = datetime.utcnow() + timedelta(hours=24)
        
        # Update user with reset token
        await self.collection.update_one(
            {"_id": ObjectId(user.id)},
            {
                "$set": {
                    "password_reset_token": reset_token,
                    "password_reset_expires": expires
                }
            }
        )
        
        # Send reset email (implementation would go here)
        return True

    async def confirm_reset_password(
        self,
        token: str,
        new_password: str
    ) -> bool:
        """
        Complete password reset process.
        """
        user = await self.collection.find_one({"password_reset_token": token})
        if not user:
            return False
        
        if user["password_reset_expires"] < datetime.utcnow():
            return False
        
        # Update password
        hashed_password = self.user_service.hash_password(new_password)
        await self.collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "hashed_password": hashed_password,
                    "password_reset_token": None,
                    "password_reset_expires": None
                }
            }
        )
        return True
