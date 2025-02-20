from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from app.core.config import settings
from app.services.ai_service import AIService
from app.models.suggestions import ApiSuggestion, UserContext, SuggestionFeedback

class AutoSuggestionsService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.suggestions_history = self.db.suggestions_history
        self.user_contexts = self.db.user_contexts
        self.ai_service = AIService()
        self.logger = logging.getLogger(__name__)
        self.vectorizer = TfidfVectorizer()
        self.knn = NearestNeighbors(n_neighbors=5)

    async def generate_suggestions(
        self,
        user_context: UserContext,
        api_context: Dict
    ) -> List[ApiSuggestion]:
        """Generate context-aware API suggestions."""
        try:
            # Analyze user context
            user_analysis = await self._analyze_user_context(user_context)
            
            # Analyze API context
            api_analysis = await self._analyze_api_context(api_context)
            
            # Generate personalized suggestions
            suggestions = await self._generate_personalized_suggestions(
                user_analysis,
                api_analysis
            )
            
            # Rank suggestions
            ranked_suggestions = await self._rank_suggestions(suggestions, user_context)
            
            return ranked_suggestions
        except Exception as e:
            self.logger.error(f"Suggestion generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Suggestion generation failed"
            )

    async def learn_from_feedback(
        self,
        suggestion: ApiSuggestion,
        feedback: SuggestionFeedback
    ) -> Dict:
        """Learn from user feedback on suggestions."""
        try:
            # Process feedback
            processed_feedback = await self._process_feedback(suggestion, feedback)
            
            # Update suggestion model
            await self._update_suggestion_model(processed_feedback)
            
            # Generate insights
            insights = await self._generate_feedback_insights(processed_feedback)
            
            return {
                "feedback_processed": True,
                "model_updated": True,
                "insights": insights,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Feedback processing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Feedback processing failed"
            )

    async def predict_next_actions(
        self,
        user_context: UserContext,
        recent_actions: List[Dict]
    ) -> List[ApiSuggestion]:
        """Predict user's next likely API actions."""
        try:
            # Analyze action patterns
            patterns = await self._analyze_action_patterns(recent_actions)
            
            # Generate predictions
            predictions = await self._generate_predictions(patterns, user_context)
            
            # Filter relevant suggestions
            filtered = await self._filter_predictions(predictions, user_context)
            
            return filtered
        except Exception as e:
            self.logger.error(f"Action prediction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Action prediction failed"
            )

    async def generate_workflow_suggestions(
        self,
        current_task: Dict,
        user_history: List[Dict]
    ) -> List[ApiSuggestion]:
        """Generate workflow-based API suggestions."""
        try:
            # Analyze task context
            task_analysis = await self._analyze_task_context(current_task)
            
            # Analyze user history
            history_analysis = await self._analyze_user_history(user_history)
            
            # Generate workflow suggestions
            suggestions = await self._generate_workflow_suggestions(
                task_analysis,
                history_analysis
            )
            
            return suggestions
        except Exception as e:
            self.logger.error(f"Workflow suggestion failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Workflow suggestion failed"
            )

    async def _analyze_user_context(self, context: UserContext) -> Dict:
        """Analyze user context for personalization."""
        try:
            # Extract user preferences
            preferences = await self.ai_service.extract_preferences(context)
            
            # Analyze usage patterns
            patterns = await self.ai_service.analyze_usage_patterns(context)
            
            # Identify user expertise
            expertise = await self.ai_service.identify_expertise(context)
            
            return {
                "preferences": preferences,
                "patterns": patterns,
                "expertise": expertise
            }
        except Exception as e:
            self.logger.error(f"Context analysis failed: {str(e)}")
            raise

    async def _analyze_api_context(self, context: Dict) -> Dict:
        """Analyze API context for relevance."""
        try:
            # Extract API features
            features = await self.ai_service.extract_api_features(context)
            
            # Analyze dependencies
            dependencies = await self.ai_service.analyze_dependencies(context)
            
            # Identify common use cases
            use_cases = await self.ai_service.identify_use_cases(context)
            
            return {
                "features": features,
                "dependencies": dependencies,
                "use_cases": use_cases
            }
        except Exception as e:
            self.logger.error(f"API context analysis failed: {str(e)}")
            raise

    async def _generate_personalized_suggestions(
        self,
        user_analysis: Dict,
        api_analysis: Dict
    ) -> List[ApiSuggestion]:
        """Generate personalized API suggestions."""
        try:
            suggestions = []
            
            # Generate based on preferences
            pref_suggestions = await self.ai_service.generate_preference_suggestions(
                user_analysis["preferences"],
                api_analysis["features"]
            )
            suggestions.extend(pref_suggestions)
            
            # Generate based on patterns
            pattern_suggestions = await self.ai_service.generate_pattern_suggestions(
                user_analysis["patterns"],
                api_analysis["use_cases"]
            )
            suggestions.extend(pattern_suggestions)
            
            # Generate based on expertise
            expertise_suggestions = await self.ai_service.generate_expertise_suggestions(
                user_analysis["expertise"],
                api_analysis["dependencies"]
            )
            suggestions.extend(expertise_suggestions)
            
            return suggestions
        except Exception as e:
            self.logger.error(f"Suggestion generation failed: {str(e)}")
            raise

    async def _rank_suggestions(
        self,
        suggestions: List[ApiSuggestion],
        context: UserContext
    ) -> List[ApiSuggestion]:
        """Rank suggestions based on relevance."""
        try:
            # Calculate relevance scores
            scores = await self._calculate_relevance_scores(suggestions, context)
            
            # Sort by score
            ranked = sorted(
                zip(suggestions, scores),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [suggestion for suggestion, _ in ranked]
        except Exception as e:
            self.logger.error(f"Suggestion ranking failed: {str(e)}")
            raise

    async def _process_feedback(
        self,
        suggestion: ApiSuggestion,
        feedback: SuggestionFeedback
    ) -> Dict:
        """Process user feedback for learning."""
        try:
            # Extract feedback features
            features = await self.ai_service.extract_feedback_features(feedback)
            
            # Analyze feedback sentiment
            sentiment = await self.ai_service.analyze_feedback_sentiment(feedback)
            
            # Generate learning points
            learning = await self.ai_service.generate_learning_points(
                suggestion,
                feedback,
                sentiment
            )
            
            return {
                "features": features,
                "sentiment": sentiment,
                "learning": learning
            }
        except Exception as e:
            self.logger.error(f"Feedback processing failed: {str(e)}")
            raise

    async def _update_suggestion_model(self, processed_feedback: Dict) -> None:
        """Update suggestion model based on feedback."""
        try:
            # Update feature weights
            await self._update_feature_weights(processed_feedback["features"])
            
            # Update sentiment analysis
            await self._update_sentiment_model(processed_feedback["sentiment"])
            
            # Apply learning points
            await self._apply_learning_points(processed_feedback["learning"])
        except Exception as e:
            self.logger.error(f"Model update failed: {str(e)}")
            raise

    async def _analyze_action_patterns(self, actions: List[Dict]) -> Dict:
        """Analyze user action patterns."""
        try:
            # Extract sequence patterns
            sequences = await self.ai_service.extract_sequences(actions)
            
            # Analyze timing patterns
            timing = await self.ai_service.analyze_timing(actions)
            
            # Identify common workflows
            workflows = await self.ai_service.identify_workflows(actions)
            
            return {
                "sequences": sequences,
                "timing": timing,
                "workflows": workflows
            }
        except Exception as e:
            self.logger.error(f"Pattern analysis failed: {str(e)}")
            raise
