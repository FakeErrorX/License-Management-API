from typing import Dict
from fastapi import APIRouter, Depends
from app.services.ai_testing import AITestingService
from app.core.deps import get_current_user
from app.models.auth import UserInDB

router = APIRouter()

@router.post("/generate")
async def generate_test_cases(
    api_spec: Dict,
    coverage_target: float = 0.9,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate AI-driven test cases."""
    testing_service = AITestingService()
    return await testing_service.generate_test_cases(api_spec, coverage_target)

@router.post("/execute/{test_suite_id}")
async def execute_test_suite(
    test_suite_id: str,
    environment: str = "staging",
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Execute AI-driven test suite."""
    testing_service = AITestingService()
    return await testing_service.execute_test_suite(test_suite_id, environment)

@router.post("/optimize/{test_suite_id}")
async def optimize_test_suite(
    test_suite_id: str,
    optimization_goals: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Optimize test suite using AI."""
    testing_service = AITestingService()
    return await testing_service.optimize_test_suite(test_suite_id, optimization_goals)

@router.get("/coverage/{test_suite_id}")
async def analyze_test_coverage(
    test_suite_id: str,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Analyze test coverage using AI."""
    testing_service = AITestingService()
    return await testing_service.analyze_test_coverage(test_suite_id)

@router.post("/regression")
async def generate_regression_tests(
    api_changes: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate regression tests for API changes."""
    testing_service = AITestingService()
    return await testing_service.generate_regression_tests(api_changes)
