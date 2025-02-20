from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from datetime import datetime
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import tensorflow as tf
from app.core.config import settings
from app.services.ai_service import AIService
from app.models.learning import LearningModel, ModelMetrics, Improvement

class ContinuousLearningService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.models = self.db.learning_models
        self.metrics = self.db.model_metrics
        self.ai_service = AIService()
        self.logger = logging.getLogger(__name__)
        
        # Initialize ML models
        self.classifier = RandomForestClassifier()
        self.deep_model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])

    async def learn_from_usage(self, usage_data: Dict) -> Dict:
        """Learn from API usage patterns."""
        try:
            # Process usage data
            processed_data = await self._process_usage_data(usage_data)
            
            # Update models
            model_updates = await self._update_models(processed_data)
            
            # Evaluate improvements
            improvements = await self._evaluate_improvements(model_updates)
            
            # Store metrics
            await self._store_learning_metrics(improvements)
            
            return {
                "model_updates": model_updates,
                "improvements": improvements,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Learning from usage failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Learning from usage failed"
            )

    async def adapt_to_feedback(self, feedback_data: Dict) -> Dict:
        """Adapt API behavior based on feedback."""
        try:
            # Analyze feedback
            analysis = await self._analyze_feedback(feedback_data)
            
            # Generate adaptations
            adaptations = await self._generate_adaptations(analysis)
            
            # Apply adaptations
            results = await self._apply_adaptations(adaptations)
            
            return {
                "adaptations": adaptations,
                "results": results,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Feedback adaptation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Feedback adaptation failed"
            )

    async def optimize_performance(
        self,
        performance_metrics: Dict
    ) -> List[Improvement]:
        """Optimize API performance through learning."""
        try:
            # Analyze performance
            analysis = await self._analyze_performance(performance_metrics)
            
            # Generate optimizations
            optimizations = await self._generate_optimizations(analysis)
            
            # Apply optimizations
            improvements = await self._apply_optimizations(optimizations)
            
            return improvements
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Performance optimization failed"
            )

    async def generate_insights(self) -> Dict:
        """Generate insights from learning process."""
        try:
            # Collect learning data
            learning_data = await self._collect_learning_data()
            
            # Analyze patterns
            patterns = await self._analyze_learning_patterns(learning_data)
            
            # Generate insights
            insights = await self._generate_learning_insights(patterns)
            
            return {
                "patterns": patterns,
                "insights": insights,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Insight generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Insight generation failed"
            )

    async def _process_usage_data(self, usage_data: Dict) -> Dict:
        """Process and normalize usage data."""
        try:
            # Extract features
            features = await self.ai_service.extract_usage_features(usage_data)
            
            # Normalize data
            normalized = await self.ai_service.normalize_data(features)
            
            # Validate data
            validated = await self.ai_service.validate_data(normalized)
            
            return validated
        except Exception as e:
            self.logger.error(f"Data processing failed: {str(e)}")
            raise

    async def _update_models(self, processed_data: Dict) -> Dict:
        """Update learning models with new data."""
        try:
            updates = {}
            
            # Update classifier
            classifier_update = await self._update_classifier(processed_data)
            updates["classifier"] = classifier_update
            
            # Update deep model
            deep_update = await self._update_deep_model(processed_data)
            updates["deep_model"] = deep_update
            
            return updates
        except Exception as e:
            self.logger.error(f"Model update failed: {str(e)}")
            raise

    async def _evaluate_improvements(self, model_updates: Dict) -> List[Improvement]:
        """Evaluate improvements from model updates."""
        try:
            improvements = []
            
            for model_name, update in model_updates.items():
                # Calculate metrics
                metrics = await self._calculate_metrics(model_name, update)
                
                # Generate improvement record
                improvement = Improvement(
                    model_name=model_name,
                    metrics=metrics,
                    timestamp=datetime.utcnow()
                )
                
                improvements.append(improvement)
            
            return improvements
        except Exception as e:
            self.logger.error(f"Improvement evaluation failed: {str(e)}")
            raise

    async def _analyze_feedback(self, feedback_data: Dict) -> Dict:
        """Analyze user feedback for adaptations."""
        try:
            # Extract feedback features
            features = await self.ai_service.extract_feedback_features(feedback_data)
            
            # Analyze sentiment
            sentiment = await self.ai_service.analyze_sentiment(feedback_data)
            
            # Generate insights
            insights = await self.ai_service.generate_feedback_insights(
                features,
                sentiment
            )
            
            return {
                "features": features,
                "sentiment": sentiment,
                "insights": insights
            }
        except Exception as e:
            self.logger.error(f"Feedback analysis failed: {str(e)}")
            raise

    async def _generate_adaptations(self, analysis: Dict) -> List[Dict]:
        """Generate adaptations based on feedback analysis."""
        try:
            adaptations = []
            
            # Generate feature adaptations
            feature_adaptations = await self.ai_service.generate_feature_adaptations(
                analysis["features"]
            )
            adaptations.extend(feature_adaptations)
            
            # Generate behavior adaptations
            behavior_adaptations = await self.ai_service.generate_behavior_adaptations(
                analysis["insights"]
            )
            adaptations.extend(behavior_adaptations)
            
            return adaptations
        except Exception as e:
            self.logger.error(f"Adaptation generation failed: {str(e)}")
            raise

    async def _apply_adaptations(self, adaptations: List[Dict]) -> Dict:
        """Apply generated adaptations."""
        try:
            results = {
                "successful": [],
                "failed": []
            }
            
            for adaptation in adaptations:
                try:
                    # Apply adaptation
                    await self.ai_service.apply_adaptation(adaptation)
                    results["successful"].append(adaptation)
                except Exception as e:
                    self.logger.warning(f"Adaptation failed: {str(e)}")
                    results["failed"].append(adaptation)
            
            return results
        except Exception as e:
            self.logger.error(f"Adaptation application failed: {str(e)}")
            raise

    async def _store_learning_metrics(self, improvements: List[Improvement]) -> None:
        """Store learning metrics in database."""
        try:
            for improvement in improvements:
                await self.metrics.insert_one(improvement.dict())
        except Exception as e:
            self.logger.error(f"Metric storage failed: {str(e)}")
            raise
