from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any, List
from app.core.security import oauth2_scheme
from app.models.license import (
    License,
    LicenseCreate,
    LicenseUpdate,
    LicenseValidation,
    BulkLicenseCreate
)
from app.services.licenses import LicenseService
from app.services.auth import AuthService

router = APIRouter()
license_service = LicenseService()
auth_service = AuthService()

@router.post("/generate", response_model=License)
async def generate_license(
    request: Request,
    license_in: LicenseCreate,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Generate a new license key.
    """
    current_user = await auth_service.get_current_user(token)
    return await license_service.create(license_in, current_user)

@router.post("/bulk-generate", response_model=List[License])
async def bulk_generate_licenses(
    request: Request,
    bulk_license: BulkLicenseCreate,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Generate multiple license keys in bulk.
    """
    current_user = await auth_service.get_current_user(token)
    return await license_service.bulk_create(bulk_license, current_user)

@router.get("/validate/{license_key}", response_model=LicenseValidation)
async def validate_license(
    request: Request,
    license_key: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Validate a license key.
    """
    validation_result = await license_service.validate(license_key)
    if not validation_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license key"
        )
    return validation_result

@router.put("/{license_id}", response_model=License)
async def update_license(
    request: Request,
    license_id: str,
    license_in: LicenseUpdate,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Update a license key.
    """
    current_user = await auth_service.get_current_user(token)
    license = await license_service.update(license_id, license_in, current_user)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    return license

@router.delete("/{license_id}")
async def revoke_license(
    request: Request,
    license_id: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Revoke a license key.
    """
    current_user = await auth_service.get_current_user(token)
    success = await license_service.revoke(license_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    return {"message": "License successfully revoked"}

@router.get("/user/{user_id}", response_model=List[License])
async def get_user_licenses(
    request: Request,
    user_id: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Get all licenses for a specific user.
    """
    current_user = await auth_service.get_current_user(token)
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return await license_service.get_user_licenses(user_id)

@router.post("/transfer/{license_id}/{new_user_id}")
async def transfer_license(
    request: Request,
    license_id: str,
    new_user_id: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Transfer a license to another user.
    """
    current_user = await auth_service.get_current_user(token)
    success = await license_service.transfer(license_id, new_user_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License transfer failed"
        )
    return {"message": "License successfully transferred"}

@router.get("/analytics/{license_id}")
async def get_license_analytics(
    request: Request,
    license_id: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Get analytics for a specific license.
    """
    current_user = await auth_service.get_current_user(token)
    analytics = await license_service.get_analytics(license_id, current_user)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found"
        )
    return analytics
