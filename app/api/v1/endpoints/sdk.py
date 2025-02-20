from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException
from app.services.sdk_generator import SDKGenerator
from app.core.deps import get_current_user
from app.models.auth import UserInDB

router = APIRouter()

@router.post("/generate/{language}")
async def generate_sdk(
    language: str,
    api_spec: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate SDK for a specific language."""
    generator = SDKGenerator()
    return await generator.generate_sdk(language, api_spec)

@router.post("/generate-all")
async def generate_all_sdks(
    api_spec: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate SDKs for all supported languages."""
    generator = SDKGenerator()
    return await generator.generate_multi_language_sdk(api_spec)

@router.post("/package/{language}")
async def generate_sdk_package(
    language: str,
    api_spec: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate complete SDK package with dependencies."""
    generator = SDKGenerator()
    return await generator.generate_sdk_package(language, api_spec)
