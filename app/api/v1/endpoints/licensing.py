from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.advanced_licensing import AdvancedLicensingService
from app.api.deps import get_current_user, get_db
from app.models.user import UserInDB

router = APIRouter()

@router.post("/user-based")
async def create_user_based_license(
    features: List[str],
    max_users: int = Query(..., gt=0),
    duration_days: int = Query(..., gt=0),
    current_user: UserInDB = Depends(get_current_user),
    licensing_service: AdvancedLicensingService = Depends(lambda: AdvancedLicensingService(get_db()))
) -> Dict:
    """Create a user-based license."""
    return await licensing_service.create_user_based_license(
        current_user,
        features,
        max_users,
        duration_days
    )

@router.post("/project-based")
async def create_project_based_license(
    project_id: str,
    features: List[str],
    max_projects: int = Query(..., gt=0),
    duration_days: int = Query(..., gt=0),
    current_user: UserInDB = Depends(get_current_user),
    licensing_service: AdvancedLicensingService = Depends(lambda: AdvancedLicensingService(get_db()))
) -> Dict:
    """Create a project-based license."""
    return await licensing_service.create_project_based_license(
        current_user,
        project_id,
        features,
        max_projects,
        duration_days
    )

@router.post("/time-limited-feature")
async def create_time_limited_feature(
    feature_id: str,
    duration_hours: int = Query(..., gt=0),
    current_user: UserInDB = Depends(get_current_user),
    licensing_service: AdvancedLicensingService = Depends(lambda: AdvancedLicensingService(get_db()))
) -> Dict:
    """Create time-limited feature access."""
    return await licensing_service.create_time_limited_feature(
        current_user,
        feature_id,
        duration_hours
    )

@router.post("/offline-license")
async def create_offline_license(
    features: List[str],
    device_id: str,
    duration_days: int = Query(..., gt=0),
    current_user: UserInDB = Depends(get_current_user),
    licensing_service: AdvancedLicensingService = Depends(lambda: AdvancedLicensingService(get_db()))
) -> Dict:
    """Create an offline license."""
    return await licensing_service.create_offline_license(
        current_user,
        features,
        duration_days,
        device_id
    )

@router.get("/verify/{license_id}")
async def verify_license(
    license_id: str,
    feature: str = None,
    licensing_service: AdvancedLicensingService = Depends(lambda: AdvancedLicensingService(get_db()))
) -> Dict:
    """Verify a license and optionally check feature access."""
    return await licensing_service.verify_license(license_id, feature)

@router.post("/transfer/{license_id}")
async def transfer_license(
    license_id: str,
    to_user_id: str,
    current_user: UserInDB = Depends(get_current_user),
    licensing_service: AdvancedLicensingService = Depends(lambda: AdvancedLicensingService(get_db()))
) -> Dict:
    """Transfer a license to another user."""
    return await licensing_service.transfer_license(
        license_id,
        str(current_user.id),
        to_user_id
    )
