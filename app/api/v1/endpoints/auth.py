from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any
from datetime import timedelta
import pyotp

from app.core.security import oauth2_scheme
from app.core.config import settings
from app.models.auth import (
    Token,
    TokenPayload,
    UserCreate,
    UserLogin,
    TwoFactorSetup,
    TwoFactorVerify
)
from app.services.auth import AuthService
from app.services.users import UserService

router = APIRouter()
auth_service = AuthService()
user_service = UserService()

@router.post("/register", response_model=Token)
async def register(request: Request, user_in: UserCreate) -> Any:
    """
    Register a new user.
    """
    user = await user_service.create(user_in)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = request.app.state.security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login.
    """
    user = await auth_service.authenticate(
        email=form_data.username,
        password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if 2FA is enabled
    if user.two_factor_enabled:
        return {
            "access_token": "2fa_required",
            "token_type": "bearer",
            "user_id": str(user.id)
        }
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = request.app.state.security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Setup 2FA for a user.
    """
    current_user = await auth_service.get_current_user(token)
    
    # Generate 2FA secret
    secret = request.app.state.security.generate_2fa_secret()
    qr_code = request.app.state.security.generate_2fa_qr(
        secret=secret,
        email=current_user.email
    )
    
    # Store secret temporarily (implement proper storage in production)
    await user_service.store_2fa_secret(current_user.id, secret)
    
    return {
        "secret": secret,
        "qr_code": qr_code
    }

@router.post("/2fa/verify", response_model=Token)
async def verify_2fa(
    request: Request,
    verify_data: TwoFactorVerify
) -> Any:
    """
    Verify 2FA token and complete login.
    """
    user = await user_service.get(verify_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify 2FA token
    if not request.app.state.security.verify_2fa_token(
        user.two_factor_secret,
        verify_data.token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 2FA token"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = request.app.state.security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/oauth/{provider}")
async def oauth_login(provider: str, request: Request) -> Any:
    """
    OAuth2 login for various providers (Google, GitHub, Microsoft).
    """
    return await auth_service.oauth_login(provider, request)

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Refresh access token.
    """
    try:
        payload = request.app.state.security.verify_token(token)
        token_data = TokenPayload(**payload)
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await user_service.get(token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = request.app.state.security.create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Logout user and invalidate token.
    """
    await auth_service.logout(token)
    return {"message": "Successfully logged out"}
