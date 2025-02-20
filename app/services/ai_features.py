from typing import Dict, List, Optional
from fastapi import HTTPException
import numpy as np
from datetime import datetime
import tensorflow as tf
from transformers import pipeline
from app.core.config import settings
from app.models.user import UserInDB

class AIFeatureService:
    def __init__(self, db):
        self.db = db
        self.ai_logs = self.db.ai_logs
        self.api_calls = self.db.api_calls
        self.errors = self.db.errors

        # Initialize AI models
        self.sentiment_analyzer = pipeline("sentiment-analysis")
        self.text_generator = pipeline("text-generation")
        self.error_classifier = self._load_error_classifier()

    def _load_error_classifier(self):
        """Load or create error classification model."""
        try:
            model = tf.keras.models.Sequential([
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(64, activation='relu'),
                tf.keras.layers.Dense(32, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
            return model
        except Exception as e:
            print(f"Error loading classifier: {str(e)}")
            return None

    async def generate_api_recommendations(self, user: UserInDB) -> Dict:
        """Generate personalized API recommendations based on usage patterns."""
        try:
            # Get user's API usage history
            usage_history = await self.api_calls.find({
                "user_id": user.id
            }).sort("timestamp", -1).limit(100).to_list(None)

            # Analyze patterns
            endpoint_frequencies = {}
            for call in usage_history:
                endpoint = call["endpoint"]
                endpoint_frequencies[endpoint] = endpoint_frequencies.get(endpoint, 0) + 1

            # Generate recommendations
            recommendations = []
            for endpoint, freq in sorted(endpoint_frequencies.items(), key=lambda x: x[1], reverse=True):
                similar_endpoints = await self._find_similar_endpoints(endpoint)
                recommendations.extend(similar_endpoints)

            return {
                "personalized_recommendations": recommendations[:5],
                "usage_patterns": endpoint_frequencies,
                "recommendation_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate API recommendations: {str(e)}"
            )

    async def analyze_api_feedback(self, feedback: str) -> Dict:
        """Analyze API feedback using sentiment analysis."""
        try:
            # Perform sentiment analysis
            sentiment = self.sentiment_analyzer(feedback)[0]
            
            # Store feedback analysis
            await self.ai_logs.insert_one({
                "type": "feedback_analysis",
                "feedback": feedback,
                "sentiment": sentiment,
                "timestamp": datetime.now()
            })

            return {
                "sentiment": sentiment["label"],
                "confidence": sentiment["score"],
                "feedback_length": len(feedback),
                "analysis_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze feedback: {str(e)}"
            )

    async def predict_api_failures(self, endpoint: str) -> Dict:
        """Predict potential API failures using machine learning."""
        try:
            # Get recent error history
            recent_errors = await self.errors.find({
                "endpoint": endpoint
            }).sort("timestamp", -1).limit(1000).to_list(None)

            if not recent_errors:
                return {
                    "risk_level": "low",
                    "confidence": 0.95,
                    "prediction_timestamp": datetime.now().isoformat()
                }

            # Extract features
            features = self._extract_error_features(recent_errors)
            
            # Make prediction
            if self.error_classifier:
                prediction = self.error_classifier.predict(features)
                risk_level = "high" if prediction[0][0] > 0.5 else "low"
                confidence = float(prediction[0][0])
            else:
                risk_level = "unknown"
                confidence = 0.0

            return {
                "risk_level": risk_level,
                "confidence": confidence,
                "prediction_timestamp": datetime.now().isoformat(),
                "analyzed_errors": len(recent_errors)
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to predict API failures: {str(e)}"
            )

    async def generate_api_documentation(self, endpoint: str) -> Dict:
        """Generate API documentation using AI."""
        try:
            # Get endpoint information
            endpoint_info = await self.api_calls.find_one({"endpoint": endpoint})
            
            if not endpoint_info:
                raise HTTPException(
                    status_code=404,
                    detail=f"Endpoint {endpoint} not found"
                )

            # Generate documentation
            prompt = f"Write API documentation for endpoint: {endpoint}\n"
            documentation = self.text_generator(prompt, max_length=500)[0]["generated_text"]

            return {
                "endpoint": endpoint,
                "documentation": documentation,
                "generation_timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate documentation: {str(e)}"
            )

    async def _find_similar_endpoints(self, endpoint: str) -> List[str]:
        """Find similar endpoints based on usage patterns."""
        all_endpoints = await self.api_calls.distinct("endpoint")
        # Implement similarity logic here
        return [e for e in all_endpoints if e != endpoint][:3]

    def _extract_error_features(self, errors: List[Dict]) -> np.ndarray:
        """Extract features from error history for prediction."""
        # Implement feature extraction logic here
        return np.array([[1.0] for _ in errors])
