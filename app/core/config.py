from pydantic_settings import BaseSettings
from typing import List, Optional
from pydantic import AnyHttpUrl, validator
import secrets
from functools import lru_cache
import os

class Settings(BaseSettings):
    # API Settings
    API_VERSION: str = "v1"
    PROJECT_NAME: str = "License Management API"
    DEBUG: bool = False
    
    # Security
    JWT_SECRET: str = secrets.token_urlsafe(32)
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    API_KEY_SALT: str = secrets.token_urlsafe(16)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # MongoDB
    MONGODB_URL: str
    MONGODB_DATABASE: str = "license_management"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Rate Limiting
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    RATE_LIMIT_MAX_REQUESTS: int = 1000
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    # OAuth2 Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    
    # Payment Integration
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    
    # bKash Configuration
    BKASH_BASE_URL: str = os.getenv("BKASH_BASE_URL", "https://tokenized.sandbox.bka.sh/v1.2.0-beta")
    BKASH_APP_KEY: str = os.getenv("BKASH_APP_KEY", "")
    BKASH_APP_SECRET: str = os.getenv("BKASH_APP_SECRET", "")
    BKASH_USERNAME: str = os.getenv("BKASH_USERNAME", "")
    BKASH_PASSWORD: str = os.getenv("BKASH_PASSWORD", "")
    
    # Email Settings
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 9090
    
    # Feature Flags
    ENABLE_AI_FEATURES: bool = True
    ENABLE_BLOCKCHAIN: bool = False
    ENABLE_2FA: bool = True
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    class Config:
        case_sensitive = True
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
