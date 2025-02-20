from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from app.services.multi_region import MultiRegionService
from app.api.deps import get_current_user, get_db
from app.models.user import UserInDB

router = APIRouter()

@router.post("/register")
async def register_region(
    region_id: str,
    endpoint: str,
    location: Dict[str, float],
    capacity: Dict[str, int],
    current_user: UserInDB = Depends(get_current_user),
    multi_region_service: MultiRegionService = Depends(lambda: MultiRegionService(get_db()))
):
    """Register a new API region."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    return await multi_region_service.register_region(
        region_id,
        endpoint,
        location,
        capacity
    )

@router.get("/nearest")
async def get_nearest_region(
    latitude: float,
    longitude: float,
    multi_region_service: MultiRegionService = Depends(lambda: MultiRegionService(get_db()))
):
    """Get the nearest available region."""
    return await multi_region_service.get_nearest_region({
        "latitude": latitude,
        "longitude": longitude
    })

@router.post("/{region_id}/load")
async def update_region_load(
    region_id: str,
    current_load: int,
    current_user: UserInDB = Depends(get_current_user),
    multi_region_service: MultiRegionService = Depends(lambda: MultiRegionService(get_db()))
):
    """Update the current load of a region."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    return await multi_region_service.update_region_load(region_id, current_load)

@router.get("/route")
async def route_request(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    preferred_region: Optional[str] = None,
    multi_region_service: MultiRegionService = Depends(lambda: MultiRegionService(get_db()))
):
    """Route an API request to the most appropriate region."""
    user_location = None
    if latitude is not None and longitude is not None:
        user_location = {
            "latitude": latitude,
            "longitude": longitude
        }
    return await multi_region_service.route_request(user_location, preferred_region)
