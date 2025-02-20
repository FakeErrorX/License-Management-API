from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from motor.motor_asyncio import AsyncIOMotorClient
import sentry_sdk
from prometheus_client import make_asgi_app
import asyncio

from app.core.config import settings
from app.core.security import setup_security
from app.api.v1.api import api_router
from app.core.middleware import (
    RateLimitMiddleware,
    APIKeyMiddleware,
    LoggingMiddleware,
    EncryptionMiddleware
)
from app.monitoring.metrics import api_version
from app.core.feature_implementation import initialize_missing_features
from app.core.monitoring import feature_monitor

# Initialize Sentry
if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Enterprise-Grade License Management System",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=None,
    redoc_url=None,
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(EncryptionMiddleware)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include API router
app.include_router(api_router, prefix=f"/api/{settings.API_VERSION}")

# Set API version info
api_version.info({
    "version": settings.VERSION,
    "environment": settings.ENVIRONMENT
})

@app.on_event("startup")
async def startup_event():
    # Initialize missing features
    initialize_missing_features()
    
    # Start feature monitoring
    asyncio.create_task(feature_monitor.monitor_features())
    
    # Initialize MongoDB connection
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongodb = app.mongodb_client[settings.MONGODB_DATABASE]
    
    # Setup security features
    await setup_security(app)

@app.on_event("shutdown")
async def shutdown_event():
    # Close MongoDB connection
    app.mongodb_client.close()

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the error and notify through Sentry if configured
    if settings.SENTRY_DSN:
        sentry_sdk.capture_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
