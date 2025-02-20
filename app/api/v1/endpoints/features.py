from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any
from app.core.feature_tracker import FeatureTracker, FeatureStatus
from app.core.feature_implementation import get_implementation_status
from app.core.deps import get_current_admin_user
from app.core.health_checks import FeatureHealthCheck

router = APIRouter()

@router.get("/status", response_model=Dict[str, List[FeatureTracker]])
async def get_feature_status(
    current_admin = Depends(get_current_admin_user)
):
    """
    Get the implementation status of all features
    """
    return get_implementation_status()

@router.post("/update/{feature_name}")
async def update_feature_status(
    feature_name: str,
    status: FeatureStatus,
    current_admin = Depends(get_current_admin_user)
):
    """
    Update the status of a specific feature
    """
    feature = feature_registry.get_feature(feature_name)
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    feature_registry.update_status(feature_name, status)
    return {"message": f"Feature {feature_name} status updated to {status.value}"}

@router.get("/health", response_model=Dict[str, Any])
async def get_feature_health(
    current_admin = Depends(get_current_admin_user)
):
    """
    Get detailed health status for all features
    """
    return feature_monitor.get_health_status()

@router.get("/health/{feature_name}")
async def get_specific_feature_health(
    feature_name: str,
    current_admin = Depends(get_current_admin_user)
):
    """
    Get health status for a specific feature
    """
    health_status = await FeatureHealthCheck.get_feature_health(feature_name)
    return health_status 