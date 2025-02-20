from typing import Dict, Optional
from fastapi import HTTPException
from httpx import AsyncClient
from app.core.config import settings
from app.models.user import UserInDB

class OAuthService:
    def __init__(self, db):
        self.db = db
        self.users = self.db.users
        self.oauth_accounts = self.db.oauth_accounts
        self.http_client = AsyncClient()

    async def google_login(self, token: str) -> Dict:
        """Handle Google OAuth2 login."""
        try:
            # Verify Google token
            response = await self.http_client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Google token")

            user_info = response.json()
            return await self._handle_oauth_user(
                provider="google",
                provider_user_id=user_info["sub"],
                email=user_info["email"],
                name=user_info.get("name")
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Google login failed: {str(e)}"
            )

    async def github_login(self, code: str) -> Dict:
        """Handle GitHub OAuth2 login."""
        try:
            # Exchange code for token
            token_response = await self.http_client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code
                },
                headers={"Accept": "application/json"}
            )
            if token_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid GitHub code")

            token_data = token_response.json()
            access_token = token_data["access_token"]

            # Get user info
            user_response = await self.http_client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/json"
                }
            )
            if user_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Failed to get GitHub user info")

            user_info = user_response.json()
            return await self._handle_oauth_user(
                provider="github",
                provider_user_id=str(user_info["id"]),
                email=user_info["email"],
                name=user_info["name"] or user_info["login"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"GitHub login failed: {str(e)}"
            )

    async def microsoft_login(self, token: str) -> Dict:
        """Handle Microsoft OAuth2 login."""
        try:
            # Get user info from Microsoft Graph API
            response = await self.http_client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid Microsoft token")

            user_info = response.json()
            return await self._handle_oauth_user(
                provider="microsoft",
                provider_user_id=user_info["id"],
                email=user_info["userPrincipalName"],
                name=user_info.get("displayName")
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Microsoft login failed: {str(e)}"
            )

    async def _handle_oauth_user(
        self,
        provider: str,
        provider_user_id: str,
        email: str,
        name: Optional[str] = None
    ) -> Dict:
        """Handle OAuth user creation or login."""
        # Check if OAuth account exists
        oauth_account = await self.oauth_accounts.find_one({
            "provider": provider,
            "provider_user_id": provider_user_id
        })

        if oauth_account:
            # Get existing user
            user = await self.users.find_one({"_id": oauth_account["user_id"]})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
        else:
            # Check if user exists with email
            user = await self.users.find_one({"email": email})
            if not user:
                # Create new user
                user = {
                    "email": email,
                    "name": name,
                    "is_active": True,
                    "is_verified": True  # Email is verified through OAuth
                }
                result = await self.users.insert_one(user)
                user["_id"] = result.inserted_id

            # Create OAuth account
            oauth_account = {
                "provider": provider,
                "provider_user_id": provider_user_id,
                "user_id": user["_id"]
            }
            await self.oauth_accounts.insert_one(oauth_account)

        # Return user data with JWT token
        from app.core.security import create_access_token
        access_token = create_access_token(str(user["_id"]))

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user["_id"]),
                "email": user["email"],
                "name": user.get("name"),
                "is_active": user["is_active"],
                "is_verified": user["is_verified"]
            }
        }
