from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import json
from typing import Optional
import redis
from prometheus_client import Counter, Histogram
from app.core.config import settings

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.window = settings.RATE_LIMIT_WINDOW
        self.max_requests = settings.RATE_LIMIT_MAX_REQUESTS

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting for certain endpoints
        if request.url.path in ["/metrics", "/health"]:
            return await call_next(request)

        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Get current request count
        current = self.redis_client.get(key)
        if current is None:
            self.redis_client.setex(key, self.window, 1)
        elif int(current) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        else:
            self.redis_client.incr(key)
        
        response = await call_next(request)
        return response

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip API key check for certain endpoints
        if request.url.path in ["/docs", "/redoc", "/metrics", "/health"]:
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key missing"
            )

        # Verify API key (implementation in security.py)
        security = request.app.state.security
        if not await self.verify_api_key(api_key, security):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        return await call_next(request)

    async def verify_api_key(self, api_key: str, security) -> bool:
        # Implementation would check against database
        # This is a placeholder
        return True

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # Get request body if present
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                body = await request.body()

        response = await call_next(request)
        
        # Calculate request duration
        duration = time.time() - start_time
        
        # Update Prometheus metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Log request details
        log_data = {
            "timestamp": time.time(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
            "ip": request.client.host,
            "user_agent": request.headers.get("user-agent"),
            "body": body
        }
        
        # In production, you would use a proper logging system
        print(json.dumps(log_data))
        
        return response

class EncryptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip encryption for certain endpoints
        if request.url.path in ["/metrics", "/health"]:
            return await call_next(request)

        # Decrypt request body if present
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                if "encrypted_data" in body:
                    security = request.app.state.security
                    decrypted_data = security.decrypt_data(body["encrypted_data"])
                    # Modify request with decrypted data
                    # Implementation depends on your needs
            except:
                pass

        response = await call_next(request)
        
        # Encrypt response if needed
        # Implementation depends on your needs
        
        return response
