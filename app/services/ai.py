from datetime import datetime, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import HTTPException, status
import numpy as np
from sklearn.ensemble import IsolationForest
from app.core.config import settings

class AIService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.usage_collection = self.db.license_usage
        self.anomaly_collection = self.db.anomalies
        self.model = IsolationForest(contamination=0.1, random_state=42)

    async def detect_license_fraud(self, license_id: str) -> Dict:
        """
        Detect potential fraudulent usage of a license.
        """
        # Get usage patterns for the last 30 days
        start_date = datetime.utcnow() - timedelta(days=30)
        usage_data = await self.usage_collection.find({
            "license_id": license_id,
            "timestamp": {"$gte": start_date}
        }).to_list(None)

        if not usage_data:
            return {
                "fraud_detected": False,
                "confidence": 0.0,
                "reasons": ["Insufficient data for analysis"]
            }

        # Extract features for analysis
        features = self._extract_fraud_features(usage_data)
        
        # Train and predict
        try:
            self.model.fit(features)
            predictions = self.model.predict(features)
            scores = self.model.score_samples(features)
            
            # Analyze results
            fraud_detected = any(pred == -1 for pred in predictions)
            confidence = float(np.abs(np.mean(scores)))
            
            reasons = self._analyze_fraud_patterns(usage_data, predictions, scores)
            
            # Store results
            await self._store_fraud_detection_result(
                license_id,
                fraud_detected,
                confidence,
                reasons
            )
            
            return {
                "fraud_detected": fraud_detected,
                "confidence": confidence,
                "reasons": reasons
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in fraud detection: {str(e)}"
            )

    def _extract_fraud_features(self, usage_data: List[Dict]) -> np.ndarray:
        """
        Extract relevant features for fraud detection.
        """
        features = []
        for usage in usage_data:
            feature_vector = [
                usage.get("usage_count", 0),
                len(usage.get("ip_addresses", [])),
                len(usage.get("device_ids", [])),
                usage.get("api_calls", 0),
                usage.get("failed_validations", 0)
            ]
            features.append(feature_vector)
        return np.array(features)

    def _analyze_fraud_patterns(
        self,
        usage_data: List[Dict],
        predictions: np.ndarray,
        scores: np.ndarray
    ) -> List[str]:
        """
        Analyze patterns to determine reasons for fraud detection.
        """
        reasons = []
        
        # Analyze usage patterns
        if len(set(d.get("ip_addresses", []) for d in usage_data)) > 10:
            reasons.append("Unusual number of IP addresses")
        
        if len(set(d.get("device_ids", []) for d in usage_data)) > 5:
            reasons.append("Unusual number of devices")
        
        # Analyze API usage
        api_calls = [d.get("api_calls", 0) for d in usage_data]
        if np.std(api_calls) > np.mean(api_calls) * 2:
            reasons.append("Irregular API usage pattern")
        
        # Analyze validation failures
        failed_validations = [d.get("failed_validations", 0) for d in usage_data]
        if sum(failed_validations) > len(failed_validations) * 0.1:
            reasons.append("High rate of validation failures")
        
        return reasons

    async def _store_fraud_detection_result(
        self,
        license_id: str,
        fraud_detected: bool,
        confidence: float,
        reasons: List[str]
    ) -> None:
        """
        Store fraud detection results for future analysis.
        """
        await self.anomaly_collection.insert_one({
            "license_id": license_id,
            "timestamp": datetime.utcnow(),
            "fraud_detected": fraud_detected,
            "confidence": confidence,
            "reasons": reasons
        })

    async def predict_license_usage(self, license_id: str) -> Dict:
        """
        Predict future license usage based on historical data.
        """
        # Get historical usage data
        usage_data = await self.usage_collection.find({
            "license_id": license_id
        }).sort("timestamp", 1).to_list(None)

        if not usage_data:
            return {
                "prediction": None,
                "confidence": 0.0,
                "message": "Insufficient data for prediction"
            }

        try:
            # Extract time series data
            timestamps = [u["timestamp"] for u in usage_data]
            values = [u["usage_count"] for u in usage_data]
            
            # Perform time series prediction
            # This is a placeholder - implement your preferred time series model
            prediction = np.mean(values) * 1.1  # Simple prediction
            confidence = 0.7  # Placeholder confidence
            
            return {
                "prediction": float(prediction),
                "confidence": confidence,
                "next_month_estimate": float(prediction * 30),
                "trend": "increasing" if prediction > np.mean(values) else "decreasing"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in usage prediction: {str(e)}"
            )

    async def analyze_user_behavior(self, user_id: str) -> Dict:
        """
        Analyze user behavior patterns.
        """
        # Get user's license usage data
        month_ago = datetime.utcnow() - timedelta(days=30)
        usage_data = await self.usage_collection.find({
            "user_id": user_id,
            "timestamp": {"$gte": month_ago}
        }).to_list(None)

        if not usage_data:
            return {
                "analysis": None,
                "message": "Insufficient data for analysis"
            }

        try:
            # Analyze usage patterns
            total_usage = sum(u["usage_count"] for u in usage_data)
            avg_daily_usage = total_usage / 30
            peak_usage = max(u["usage_count"] for u in usage_data)
            
            # Analyze time patterns
            usage_hours = [u["timestamp"].hour for u in usage_data]
            peak_hours = self._find_peak_hours(usage_hours)
            
            # Generate insights
            insights = self._generate_behavior_insights(
                avg_daily_usage,
                peak_usage,
                peak_hours,
                usage_data
            )
            
            return {
                "analysis": {
                    "total_usage": total_usage,
                    "avg_daily_usage": float(avg_daily_usage),
                    "peak_usage": peak_usage,
                    "peak_hours": peak_hours,
                    "usage_pattern": "regular" if np.std([u["usage_count"] for u in usage_data]) < avg_daily_usage else "irregular"
                },
                "insights": insights
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in behavior analysis: {str(e)}"
            )

    def _find_peak_hours(self, usage_hours: List[int]) -> List[int]:
        """
        Find peak usage hours.
        """
        hour_counts = np.bincount(usage_hours)
        peak_threshold = np.mean(hour_counts) + np.std(hour_counts)
        return [hour for hour, count in enumerate(hour_counts) if count > peak_threshold]

    def _generate_behavior_insights(
        self,
        avg_daily_usage: float,
        peak_usage: int,
        peak_hours: List[int],
        usage_data: List[Dict]
    ) -> List[str]:
        """
        Generate insights based on user behavior.
        """
        insights = []
        
        # Usage pattern insights
        if peak_usage > avg_daily_usage * 3:
            insights.append("Significant usage spikes detected")
        
        # Time pattern insights
        if len(peak_hours) <= 4:
            insights.append("Usage concentrated in specific hours")
        else:
            insights.append("Distributed usage pattern throughout the day")
        
        # Feature usage insights
        feature_usage = {}
        for usage in usage_data:
            for feature in usage.get("features_used", []):
                feature_usage[feature] = feature_usage.get(feature, 0) + 1
        
        most_used = max(feature_usage.items(), key=lambda x: x[1])[0]
        insights.append(f"Most frequently used feature: {most_used}")
        
        return insights
