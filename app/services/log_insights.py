from typing import Dict, List, Optional
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import logging
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import tensorflow as tf
from app.core.config import settings
from app.services.ai_service import AIService
from app.models.logs import LogInsight, LogPattern, LogAnomaly

class LogInsightsService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.logs = self.db.logs
        self.insights = self.db.log_insights
        self.ai_service = AIService()
        self.logger = logging.getLogger(__name__)
        
        # Initialize ML models
        self.anomaly_detector = DBSCAN(eps=0.3, min_samples=10)
        self.pattern_model = tf.keras.Sequential([
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])

    async def analyze_logs(
        self,
        timeframe: str = "24h",
        log_types: Optional[List[str]] = None
    ) -> List[LogInsight]:
        """Analyze API logs and generate insights."""
        try:
            # Fetch logs
            logs = await self._fetch_logs(timeframe, log_types)
            
            # Extract patterns
            patterns = await self._extract_patterns(logs)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(logs)
            
            # Generate insights
            insights = await self._generate_insights(patterns, anomalies)
            
            # Store insights
            await self._store_insights(insights)
            
            return insights
        except Exception as e:
            self.logger.error(f"Log analysis failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Log analysis failed"
            )

    async def predict_issues(
        self,
        prediction_window: str = "1h"
    ) -> List[Dict]:
        """Predict potential issues based on log patterns."""
        try:
            # Get recent patterns
            patterns = await self._get_recent_patterns()
            
            # Generate predictions
            predictions = await self._generate_predictions(patterns, prediction_window)
            
            # Assess impact
            impact = await self._assess_impact(predictions)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(impact)
            
            return {
                "predictions": predictions,
                "impact": impact,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Issue prediction failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Issue prediction failed"
            )

    async def generate_performance_insights(
        self,
        metrics: List[str],
        timeframe: str = "24h"
    ) -> Dict:
        """Generate performance insights from logs."""
        try:
            # Analyze performance metrics
            analysis = await self._analyze_performance_metrics(metrics, timeframe)
            
            # Identify bottlenecks
            bottlenecks = await self._identify_bottlenecks(analysis)
            
            # Generate optimizations
            optimizations = await self._generate_optimizations(bottlenecks)
            
            return {
                "analysis": analysis,
                "bottlenecks": bottlenecks,
                "optimizations": optimizations,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Performance analysis failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Performance analysis failed"
            )

    async def analyze_error_patterns(
        self,
        error_types: Optional[List[str]] = None,
        timeframe: str = "24h"
    ) -> Dict:
        """Analyze error patterns in logs."""
        try:
            # Extract error logs
            error_logs = await self._extract_error_logs(error_types, timeframe)
            
            # Analyze patterns
            patterns = await self._analyze_error_patterns(error_logs)
            
            # Generate solutions
            solutions = await self._generate_error_solutions(patterns)
            
            return {
                "patterns": patterns,
                "solutions": solutions,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            self.logger.error(f"Error analysis failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error analysis failed"
            )

    async def _fetch_logs(
        self,
        timeframe: str,
        log_types: Optional[List[str]]
    ) -> List[Dict]:
        """Fetch logs from database."""
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - self._parse_timeframe(timeframe)
            
            # Build query
            query = {
                "timestamp": {
                    "$gte": start_time,
                    "$lte": end_time
                }
            }
            if log_types:
                query["type"] = {"$in": log_types}
            
            # Fetch logs
            return await self.logs.find(query).to_list(None)
        except Exception as e:
            self.logger.error(f"Log fetch failed: {str(e)}")
            raise

    async def _extract_patterns(self, logs: List[Dict]) -> List[LogPattern]:
        """Extract patterns from logs using ML."""
        try:
            # Prepare data
            features = await self._extract_log_features(logs)
            
            # Scale features
            scaled_features = StandardScaler().fit_transform(features)
            
            # Train pattern model
            predictions = self.pattern_model.predict(scaled_features)
            
            # Generate patterns
            return [
                LogPattern(
                    pattern_type="sequence" if pred > 0.5 else "random",
                    confidence=float(pred),
                    logs=log_group
                )
                for pred, log_group in zip(predictions, self._group_logs(logs))
            ]
        except Exception as e:
            self.logger.error(f"Pattern extraction failed: {str(e)}")
            raise

    async def _detect_anomalies(self, logs: List[Dict]) -> List[LogAnomaly]:
        """Detect anomalies in logs using DBSCAN."""
        try:
            # Extract features
            features = await self._extract_log_features(logs)
            
            # Scale features
            scaled_features = StandardScaler().fit_transform(features)
            
            # Detect anomalies
            labels = self.anomaly_detector.fit_predict(scaled_features)
            
            # Generate anomalies
            return [
                LogAnomaly(
                    log=log,
                    anomaly_type="outlier" if label == -1 else "normal",
                    severity="high" if label == -1 else "low",
                    timestamp=log.get("timestamp", datetime.utcnow())
                )
                for label, log in zip(labels, logs)
                if label == -1
            ]
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {str(e)}")
            raise

    async def _generate_insights(
        self,
        patterns: List[LogPattern],
        anomalies: List[LogAnomaly]
    ) -> List[LogInsight]:
        """Generate insights from patterns and anomalies."""
        try:
            insights = []
            
            # Generate pattern insights
            for pattern in patterns:
                insight = await self.ai_service.generate_pattern_insight(pattern)
                insights.append(insight)
            
            # Generate anomaly insights
            for anomaly in anomalies:
                insight = await self.ai_service.generate_anomaly_insight(anomaly)
                insights.append(insight)
            
            return insights
        except Exception as e:
            self.logger.error(f"Insight generation failed: {str(e)}")
            raise

    def _parse_timeframe(self, timeframe: str) -> timedelta:
        """Parse timeframe string to timedelta."""
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        
        if unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        else:
            raise ValueError(f"Invalid timeframe unit: {unit}")

    async def _extract_log_features(self, logs: List[Dict]) -> np.ndarray:
        """Extract numerical features from logs."""
        try:
            features = []
            for log in logs:
                # Extract relevant numerical features
                feature_vector = [
                    log.get("duration", 0),
                    log.get("status_code", 0),
                    log.get("response_size", 0),
                    log.get("error_count", 0)
                ]
                features.append(feature_vector)
            return np.array(features)
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {str(e)}")
            raise

    def _group_logs(self, logs: List[Dict], window_size: int = 10) -> List[List[Dict]]:
        """Group logs into windows for pattern analysis."""
        return [
            logs[i:i + window_size]
            for i in range(0, len(logs), window_size)
        ]
