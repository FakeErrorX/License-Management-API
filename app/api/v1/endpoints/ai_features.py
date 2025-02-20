from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.ai_features import AIFeatureService
from app.api.deps import get_current_user, get_db
from app.models.user import UserInDB

router = APIRouter()

@router.get("/recommendations")
async def get_api_recommendations(
    current_user: UserInDB = Depends(get_current_user),
    ai_service: AIFeatureService = Depends(lambda: AIFeatureService(get_db()))
) -> Dict:
    """Get personalized API recommendations based on usage patterns."""
    return await ai_service.generate_api_recommendations(current_user)

@router.post("/feedback/analyze")
async def analyze_feedback(
    feedback: str = Query(..., min_length=1),
    ai_service: AIFeatureService = Depends(lambda: AIFeatureService(get_db()))
) -> Dict:
    """Analyze API feedback using sentiment analysis."""
    return await ai_service.analyze_api_feedback(feedback)

@router.get("/failures/predict")
async def predict_failures(
    endpoint: str = Query(..., min_length=1),
    ai_service: AIFeatureService = Depends(lambda: AIFeatureService(get_db()))
) -> Dict:
    """Predict potential API failures using machine learning."""
    return await ai_service.predict_api_failures(endpoint)

@router.get("/documentation/generate")
async def generate_documentation(
    endpoint: str = Query(..., min_length=1),
    ai_service: AIFeatureService = Depends(lambda: AIFeatureService(get_db()))
) -> Dict:
    """Generate API documentation using AI."""
    return await ai_service.generate_api_documentation(endpoint)
