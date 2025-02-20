from typing import Dict, Optional
from fastapi import APIRouter, Depends
from app.services.smart_caching import SmartCachingService
from app.core.deps import get_current_user
from app.models.auth import UserInDB

router = APIRouter()

@router.get("/response")
async def get_cached_response(
    request_data: Dict,
    endpoint: str,
    current_user: UserInDB = Depends(get_current_user)
) -> Optional[Dict]:
    """Get cached API response using smart caching."""
    caching_service = SmartCachingService()
    return await caching_service.get_cached_response(request_data, endpoint)

@router.post("/response")
async def cache_response(
    request_data: Dict,
    response_data: Dict,
    endpoint: str,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Cache API response with smart TTL."""
    caching_service = SmartCachingService()
    return await caching_service.cache_response(request_data, response_data, endpoint)

@router.post("/optimize/{endpoint}")
async def optimize_cache_strategy(
    endpoint: str,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Optimize caching strategy for endpoint."""
    caching_service = SmartCachingService()
    return await caching_service.optimize_cache_strategy(endpoint)

@router.get("/predict")
async def predict_cache_requirements(
    timeframe: str = "1h",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Predict future cache requirements."""
    caching_service = SmartCachingService()
    return await caching_service.predict_cache_requirements(timeframe)

@router.post("/invalidation")
async def manage_cache_invalidation(
    invalidation_rules: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Manage smart cache invalidation."""
    caching_service = SmartCachingService()
    return await caching_service.manage_cache_invalidation(invalidation_rules)
