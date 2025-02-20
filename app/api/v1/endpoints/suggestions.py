from typing import Dict, List
from fastapi import APIRouter, Depends
from app.services.auto_suggestions import AutoSuggestionsService
from app.core.deps import get_current_user
from app.models.auth import UserInDB
from app.models.suggestions import ApiSuggestion, UserContext, SuggestionFeedback

router = APIRouter()

@router.post("/generate")
async def generate_suggestions(
    user_context: UserContext,
    api_context: Dict,
    current_user: UserInDB = Depends(get_current_user)
) -> List[ApiSuggestion]:
    """Generate context-aware API suggestions."""
    suggestions_service = AutoSuggestionsService()
    return await suggestions_service.generate_suggestions(user_context, api_context)

@router.post("/feedback")
async def submit_suggestion_feedback(
    suggestion: ApiSuggestion,
    feedback: SuggestionFeedback,
    current_user: UserInDB = Depends(get_current_user)
) -> Dict:
    """Submit feedback for API suggestions."""
    suggestions_service = AutoSuggestionsService()
    return await suggestions_service.learn_from_feedback(suggestion, feedback)

@router.post("/predict")
async def predict_next_actions(
    user_context: UserContext,
    recent_actions: List[Dict],
    current_user: UserInDB = Depends(get_current_user)
) -> List[ApiSuggestion]:
    """Predict user's next likely API actions."""
    suggestions_service = AutoSuggestionsService()
    return await suggestions_service.predict_next_actions(user_context, recent_actions)

@router.post("/workflow")
async def generate_workflow_suggestions(
    current_task: Dict,
    user_history: List[Dict],
    current_user: UserInDB = Depends(get_current_user)
) -> List[ApiSuggestion]:
    """Generate workflow-based API suggestions."""
    suggestions_service = AutoSuggestionsService()
    return await suggestions_service.generate_workflow_suggestions(
        current_task,
        user_history
    )
