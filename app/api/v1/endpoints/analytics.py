from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any, Dict, List
from datetime import datetime, timedelta
from app.core.security import oauth2_scheme
from app.services.auth import AuthService
from app.services.analytics import AnalyticsService

router = APIRouter()
auth_service = AuthService()
analytics_service = AnalyticsService()

@router.get("/dashboard")
async def get_dashboard_metrics(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get overall dashboard metrics.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_dashboard_metrics(current_user)

@router.get("/api-usage")
async def get_api_usage(
    request: Request,
    start_date: datetime = None,
    end_date: datetime = None,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get API usage statistics.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_api_usage(current_user, start_date, end_date)

@router.get("/geo-metrics")
async def get_geo_metrics(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get geographical usage metrics.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_geo_metrics(current_user)

@router.get("/user-behavior")
async def get_user_behavior_metrics(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get user behavior analytics.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_user_behavior_metrics(current_user)

@router.get("/performance")
async def get_performance_metrics(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get API performance metrics.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_performance_metrics(current_user)

@router.get("/error-tracking")
async def get_error_metrics(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get error tracking metrics.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_error_metrics(current_user)

@router.get("/license-metrics")
async def get_license_metrics(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get license-related metrics.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_license_metrics(current_user)

@router.get("/revenue-metrics")
async def get_revenue_metrics(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Get revenue and financial metrics.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_revenue_metrics(current_user)

@router.post("/export")
async def export_analytics(
    request: Request,
    metrics: List[str],
    format: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Export analytics data in various formats.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.export_analytics(current_user, metrics, format)

@router.get("/alerts")
async def get_analytics_alerts(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> List[Dict]:
    """
    Get analytics-based alerts.
    """
    current_user = await auth_service.get_current_user(token)
    return await analytics_service.get_alerts(current_user)
