from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any, Dict, List
from app.core.security import oauth2_scheme
from app.services.auth import AuthService
from app.services.admin import AdminService
from app.models.auth import UserRole

router = APIRouter()
auth_service = AuthService()
admin_service = AdminService()

async def check_admin_access(token: str):
    """
    Verify admin access.
    """
    current_user = await auth_service.get_current_user(token)
    if not current_user.is_active or current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

@router.get("/dashboard")
async def get_admin_dashboard(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get admin dashboard overview.
    """
    current_user = await check_admin_access(token)
    return await admin_service.get_dashboard_metrics()

@router.get("/users")
async def get_all_users(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get all users with pagination.
    """
    await check_admin_access(token)
    return await admin_service.get_all_users(skip, limit)

@router.post("/users/{user_id}/role")
async def update_user_role(
    request: Request,
    user_id: str,
    role: UserRole,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Update user role.
    """
    current_user = await check_admin_access(token)
    return await admin_service.update_user_role(user_id, role)

@router.get("/licenses")
async def get_all_licenses(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get all licenses with pagination.
    """
    await check_admin_access(token)
    return await admin_service.get_all_licenses(skip, limit)

@router.post("/licenses/bulk-action")
async def bulk_license_action(
    request: Request,
    action: str,
    license_ids: List[str],
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Perform bulk action on licenses.
    """
    await check_admin_access(token)
    return await admin_service.bulk_license_action(action, license_ids)

@router.get("/audit-logs")
async def get_audit_logs(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get system audit logs.
    """
    await check_admin_access(token)
    return await admin_service.get_audit_logs(skip, limit)

@router.get("/system-health")
async def get_system_health(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get system health metrics.
    """
    await check_admin_access(token)
    return await admin_service.get_system_health()

@router.post("/maintenance-mode")
async def toggle_maintenance_mode(
    request: Request,
    enabled: bool,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Toggle system maintenance mode.
    """
    await check_admin_access(token)
    return await admin_service.toggle_maintenance_mode(enabled)

@router.post("/cache/clear")
async def clear_system_cache(
    request: Request,
    cache_type: str,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Clear system cache.
    """
    await check_admin_access(token)
    return await admin_service.clear_cache(cache_type)

@router.get("/security/settings")
async def get_security_settings(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get security settings.
    """
    await check_admin_access(token)
    return await admin_service.get_security_settings()

@router.post("/security/settings")
async def update_security_settings(
    request: Request,
    settings: Dict,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Update security settings.
    """
    await check_admin_access(token)
    return await admin_service.update_security_settings(settings)

@router.get("/reports")
async def generate_admin_report(
    request: Request,
    report_type: str,
    start_date: str,
    end_date: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Generate administrative reports.
    """
    await check_admin_access(token)
    return await admin_service.generate_report(report_type, start_date, end_date)

@router.post("/notifications")
async def send_admin_notification(
    request: Request,
    notification: Dict,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Send administrative notifications.
    """
    await check_admin_access(token)
    return await admin_service.send_notification(notification)

@router.get("/api-keys")
async def get_api_keys(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get all API keys.
    """
    await check_admin_access(token)
    return await admin_service.get_api_keys()

@router.post("/api-keys/rotate")
async def rotate_api_keys(
    request: Request,
    key_ids: List[str],
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Rotate specified API keys.
    """
    await check_admin_access(token)
    return await admin_service.rotate_api_keys(key_ids)

@router.get("/resellers")
async def get_resellers(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get all resellers.
    """
    await check_admin_access(token)
    return await admin_service.get_resellers()

@router.post("/resellers/{reseller_id}/commission")
async def update_reseller_commission(
    request: Request,
    reseller_id: str,
    commission_rate: float,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Update reseller commission rate.
    """
    await check_admin_access(token)
    return await admin_service.update_reseller_commission(reseller_id, commission_rate)
