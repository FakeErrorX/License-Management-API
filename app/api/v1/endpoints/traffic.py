from typing import Dict
from fastapi import APIRouter, Depends
from app.services.traffic_analysis import TrafficAnalysisService
from app.core.deps import get_current_user
from app.models.auth import UserInDB

router = APIRouter()

@router.get("/patterns")
async def analyze_traffic_patterns(
    timeframe: str = "1h",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Analyze API traffic patterns."""
    analysis_service = TrafficAnalysisService()
    return await analysis_service.analyze_traffic_patterns(timeframe)

@router.get("/predict")
async def predict_traffic_load(
    prediction_window: str = "1h",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Predict future API traffic load."""
    analysis_service = TrafficAnalysisService()
    return await analysis_service.predict_traffic_load(prediction_window)

@router.get("/endpoint/{endpoint}")
async def analyze_endpoint_usage(
    endpoint: str,
    timeframe: str = "24h",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Analyze usage patterns for specific endpoint."""
    analysis_service = TrafficAnalysisService()
    return await analysis_service.analyze_endpoint_usage(endpoint, timeframe)

@router.post("/report")
async def generate_traffic_report(
    report_config: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate comprehensive traffic analysis report."""
    analysis_service = TrafficAnalysisService()
    return await analysis_service.generate_traffic_report(report_config)

@router.post("/optimize")
async def optimize_traffic_routing(
    routing_config: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Optimize API traffic routing based on analysis."""
    analysis_service = TrafficAnalysisService()
    return await analysis_service.optimize_traffic_routing(routing_config)
