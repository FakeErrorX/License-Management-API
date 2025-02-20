from typing import Dict
from fastapi import APIRouter, Depends
from app.services.breach_prevention import BreachPreventionService
from app.core.deps import get_current_user
from app.models.auth import UserInDB

router = APIRouter()

@router.post("/breach/detect")
async def detect_breach_attempts(
    request_data: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Detect potential API breach attempts."""
    prevention_service = BreachPreventionService()
    return await prevention_service.detect_breach_attempts(request_data)

@router.post("/breach/prevent")
async def prevent_breach(
    threat_data: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Take action to prevent detected breaches."""
    prevention_service = BreachPreventionService()
    return await prevention_service.prevent_breach(threat_data)

@router.get("/breach/patterns")
async def analyze_breach_patterns(
    timeframe: str = "24h",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Analyze breach attempt patterns."""
    prevention_service = BreachPreventionService()
    return await prevention_service.analyze_breach_patterns(timeframe)

@router.post("/breach/rules/update")
async def update_prevention_rules(
    new_patterns: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Update breach prevention rules based on new patterns."""
    prevention_service = BreachPreventionService()
    return await prevention_service.update_prevention_rules(new_patterns)

@router.post("/breach/report")
async def generate_breach_report(
    report_config: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate comprehensive breach analysis report."""
    prevention_service = BreachPreventionService()
    return await prevention_service.generate_breach_report(report_config)
