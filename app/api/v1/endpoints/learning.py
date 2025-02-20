from typing import Dict, List
from fastapi import APIRouter, Depends
from app.services.continuous_learning import ContinuousLearningService
from app.core.deps import get_current_user
from app.models.auth import UserInDB
from app.models.learning import Improvement

router = APIRouter()

@router.post("/usage")
async def learn_from_usage(
    usage_data: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Learn from API usage patterns."""
    learning_service = ContinuousLearningService()
    return await learning_service.learn_from_usage(usage_data)

@router.post("/feedback")
async def adapt_to_feedback(
    feedback_data: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Adapt API behavior based on feedback."""
    learning_service = ContinuousLearningService()
    return await learning_service.adapt_to_feedback(feedback_data)

@router.post("/optimize")
async def optimize_performance(
    performance_metrics: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> List[Improvement]:
    """Optimize API performance through learning."""
    learning_service = ContinuousLearningService()
    return await learning_service.optimize_performance(performance_metrics)

@router.get("/insights")
async def generate_insights(
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Generate insights from learning process."""
    learning_service = ContinuousLearningService()
    return await learning_service.generate_insights()
