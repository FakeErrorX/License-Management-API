from typing import Dict, List
from fastapi import APIRouter, Depends, Request
from app.services.api_gateway import APIGatewayService
from app.core.deps import get_current_user
from app.models.auth import UserInDB

router = APIRouter()

@router.post("/route")
async def route_request(
    request: Request,
    target_service: str,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Route request through the API gateway."""
    gateway = APIGatewayService()
    return await gateway.route_request(request, target_service)

@router.post("/services/register")
async def register_service(
    service_info: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Register a new service in the mesh."""
    gateway = APIGatewayService()
    return await gateway.register_service(service_info)

@router.post("/circuit-breaker/configure")
async def configure_circuit_breaker(
    config: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Configure circuit breaker for a service."""
    gateway = APIGatewayService()
    return await gateway.configure_circuit_breaker(config)

@router.post("/rate-limiting/setup")
async def setup_rate_limiting(
    config: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Set up rate limiting for a service."""
    gateway = APIGatewayService()
    return await gateway.setup_rate_limiting(config)

@router.post("/mesh/configure")
async def configure_service_mesh(
    mesh_config: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Configure service mesh policies."""
    gateway = APIGatewayService()
    return await gateway.configure_service_mesh(mesh_config)
