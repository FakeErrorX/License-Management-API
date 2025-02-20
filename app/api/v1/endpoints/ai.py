from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Any, Dict
from app.core.security import oauth2_scheme
from app.services.auth import AuthService
from app.services.ai import AIService

router = APIRouter()
auth_service = AuthService()
ai_service = AIService()

@router.post("/fraud-detection/{license_id}")
async def detect_fraud(
    request: Request,
    license_id: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Detect potential fraudulent usage of a license using AI.
    """
    current_user = await auth_service.get_current_user(token)
    if not current_user.is_active or current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await ai_service.detect_license_fraud(license_id)

@router.get("/usage-prediction/{license_id}")
async def predict_usage(
    request: Request,
    license_id: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Predict future license usage based on historical data.
    """
    current_user = await auth_service.get_current_user(token)
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await ai_service.predict_license_usage(license_id)

@router.get("/behavior-analysis/{user_id}")
async def analyze_behavior(
    request: Request,
    user_id: str,
    token: str = Depends(oauth2_scheme)
) -> Any:
    """
    Analyze user behavior patterns using AI.
    """
    current_user = await auth_service.get_current_user(token)
    if not current_user.is_active or (
        current_user.role not in ["admin"] and
        str(current_user.id) != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await ai_service.analyze_user_behavior(user_id)

@router.get("/risk-assessment/{license_id}")
async def assess_risk(
    request: Request,
    license_id: str,
    token: str = Depends(oauth2_scheme)
) -> Dict:
    """
    Assess risk level for a license using AI.
    """
    current_user = await auth_service.get_current_user(token)
    if not current_user.is_active or current_user.role not in ["admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Combine multiple AI analyses for comprehensive risk assessment
    fraud_analysis = await ai_service.detect_license_fraud(license_id)
    usage_prediction = await ai_service.predict_license_usage(license_id)
    
    # Calculate risk score (0-100)
    risk_score = 0
    
    # Factor in fraud detection
    if fraud_analysis["fraud_detected"]:
        risk_score += 50 * fraud_analysis["confidence"]
    
    # Factor in usage prediction
    if usage_prediction["prediction"]:
        if usage_prediction["trend"] == "increasing":
            risk_score += 20
        if usage_prediction["confidence"] < 0.5:
            risk_score += 10
    
    # Categorize risk level
    risk_level = "low"
    if risk_score > 70:
        risk_level = "high"
    elif risk_score > 30:
        risk_level = "medium"
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "factors": {
            "fraud_analysis": fraud_analysis,
            "usage_prediction": usage_prediction
        },
        "recommendations": [
            "Monitor usage patterns more closely" if risk_score > 50 else "Regular monitoring sufficient",
            "Implement additional security measures" if fraud_analysis["fraud_detected"] else "Current security measures adequate",
            "Review license terms" if usage_prediction["trend"] == "increasing" else "License terms appropriate"
        ]
    }
