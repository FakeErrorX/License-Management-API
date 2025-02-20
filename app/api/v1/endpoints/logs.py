from typing import Dict, List, Optional
from fastapi import APIRouter, Depends
from app.services.log_insights import LogInsightsService
from app.core.deps import get_current_user
from app.models.auth import UserInDB
from app.models.logs import LogInsight

router = APIRouter()

@router.get("/analyze")
async def analyze_logs(
    timeframe: str = "24h",
    log_types: Optional[List[str]] = None,
    current_user: UserInDB = Depends(get_current_user)
) -> List[LogInsight]:
    """Analyze API logs and generate insights."""
    insights_service = LogInsightsService()
    return await insights_service.analyze_logs(timeframe, log_types)

@router.get("/predict")
async def predict_issues(
    prediction_window: str = "1h",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Predict potential issues based on log patterns."""
    insights_service = LogInsightsService()
    return await insights_service.predict_issues(prediction_window)

@router.get("/performance")
async def generate_performance_insights(
    metrics: List[str],
    timeframe: str = "24h",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate performance insights from logs."""
    insights_service = LogInsightsService()
    return await insights_service.generate_performance_insights(metrics, timeframe)

@router.get("/errors")
async def analyze_error_patterns(
    error_types: Optional[List[str]] = None,
    timeframe: str = "24h",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Analyze error patterns in logs."""
    insights_service = LogInsightsService()
    return await insights_service.analyze_error_patterns(error_types, timeframe)
