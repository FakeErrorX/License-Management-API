from fastapi import APIRouter, Depends, HTTPException
from app.services.oauth import OAuthService
from app.api.deps import get_db

router = APIRouter()

@router.post("/google")
async def google_login(
    token: str,
    oauth_service: OAuthService = Depends(lambda: OAuthService(get_db()))
):
    """Login with Google OAuth2."""
    return await oauth_service.google_login(token)

@router.post("/github")
async def github_login(
    code: str,
    oauth_service: OAuthService = Depends(lambda: OAuthService(get_db()))
):
    """Login with GitHub OAuth2."""
    return await oauth_service.github_login(code)

@router.post("/microsoft")
async def microsoft_login(
    token: str,
    oauth_service: OAuthService = Depends(lambda: OAuthService(get_db()))
):
    """Login with Microsoft OAuth2."""
    return await oauth_service.microsoft_login(token)
