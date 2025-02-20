from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    payments,
    ai_features,
    performance,
    licensing,
    oauth,
    regions,
    gateway,
    traffic,
    security,
    caching,
    testing,
    voice
)
from app.api.graphql.endpoint import router as graphql_router
from app.api.websocket.endpoints import router as websocket_router

api_router = APIRouter()

# Existing routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])

# New routes
api_router.include_router(ai_features.router, prefix="/ai", tags=["AI Features"])
api_router.include_router(performance.router, prefix="/performance", tags=["Performance"])
api_router.include_router(licensing.router, prefix="/licenses", tags=["Licensing"])
api_router.include_router(oauth.router, prefix="/oauth", tags=["OAuth"])
api_router.include_router(regions.router, prefix="/regions", tags=["Multi-Region"])

# Add gateway router
api_router.include_router(
    gateway.router,
    prefix="/gateway",
    tags=["gateway"]
)

# Add new routers
api_router.include_router(traffic.router, prefix="/traffic", tags=["Traffic Analysis"])
api_router.include_router(security.router, prefix="/security", tags=["Security"])
api_router.include_router(caching.router, prefix="/cache", tags=["Caching"])
api_router.include_router(testing.router, prefix="/testing", tags=["Testing"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice"])

# GraphQL endpoint
api_router.include_router(graphql_router, prefix="/graphql", tags=["GraphQL"])

# WebSocket endpoints
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
