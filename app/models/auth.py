from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    RESELLER = "reseller"

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[str] = None

class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    type: Optional[str] = "access"

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    confirm_password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "password": "strongpassword123",
                "confirm_password": "strongpassword123"
            }
        }

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    password_reset_token: Optional[str] = None
    password_reset_expires: Optional[datetime] = None

class TwoFactorSetup(BaseModel):
    secret: str
    qr_code: bytes

class TwoFactorVerify(BaseModel):
    user_id: str
    token: str

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

class OAuth2Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
