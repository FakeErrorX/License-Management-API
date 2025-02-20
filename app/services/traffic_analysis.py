from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import json
import asyncio
from datetime import datetime, timedelta
import openai
import numpy as np
from sklearn.cluster import KMeans
import tensorflow as tf
from transformers import AutoTokenizer, AutoModel
import pandas as pd
import requests
import logging
from prometheus_client import Counter, Histogram
import aiohttp
from app.core.config import settings

class TrafficAnalysisService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.traffic = self.db.traffic
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        
        # Initialize ML models
        self.pattern_detector = KMeans(n_clusters=5)
        self.traffic_predictor = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        
        # Initialize metrics
        self.traffic_analysis = Counter(
            'traffic_analysis_total',
            'Total number of traffic analysis operations'
        )
        self.analysis_duration = Histogram(
            'analysis_duration_seconds',
            'Duration of traffic analysis operations'
        )

    async def analyze_traffic_patterns(
        self,
        timeframe: str = "1h"
    ) -> Dict:
        """
        Analyze API traffic patterns.
        """
        try:
            # Collect traffic data
            data = await self.collect_traffic_data(timeframe)
            
            # Analyze patterns
            patterns = await self.analyze_patterns(data)
            
            # Generate insights
            insights = await self.generate_insights(patterns)
            
            return {
                "analysis_id": patterns["analysis_id"],
                "patterns": patterns["details"],
                "insights": insights,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Traffic analysis failed: {str(e)}"
            )

    async def predict_traffic_load(
        self,
        prediction_window: str = "1h"
    ) -> Dict:
        """
        Predict future API traffic load.
        """
        try:
            # Prepare data
            data = await self.prepare_prediction_data(prediction_window)
            
            # Generate prediction
            prediction = await self.generate_prediction(data)
            
            # Generate recommendations
            recommendations = await self.generate_recommendations(prediction)
            
            return {
                "prediction_id": prediction["prediction_id"],
                "forecast": prediction["forecast"],
                "recommendations": recommendations,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Traffic prediction failed: {str(e)}"
            )

    async def analyze_endpoint_usage(
        self,
        endpoint: str,
        timeframe: str = "24h"
    ) -> Dict:
        """
        Analyze usage patterns for specific endpoint.
        """
        try:
            # Collect endpoint data
            data = await self.collect_endpoint_data(endpoint, timeframe)
            
            # Analyze usage
            usage = await self.analyze_usage(data)
            
            # Generate optimization suggestions
            suggestions = await self.generate_suggestions(usage)
            
            return {
                "endpoint": endpoint,
                "usage": usage,
                "suggestions": suggestions,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Endpoint analysis failed: {str(e)}"
            )

    async def generate_traffic_report(
        self,
        report_config: Dict
    ) -> Dict:
        """
        Generate comprehensive traffic analysis report.
        """
        try:
            # Collect data
            data = await self.collect_report_data(report_config)
            
            # Generate analysis
            analysis = await self.analyze_report_data(data)
            
            # Generate visualizations
            visualizations = await self.generate_visualizations(analysis)
            
            return {
                "report_id": data["report_id"],
                "analysis": analysis,
                "visualizations": visualizations,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {str(e)}"
            )

    async def optimize_traffic_routing(
        self,
        routing_config: Dict
    ) -> Dict:
        """
        Optimize API traffic routing based on analysis.
        """
        try:
            # Analyze current routing
            analysis = await self.analyze_current_routing(routing_config)
            
            # Generate optimization plan
            plan = await self.generate_optimization_plan(analysis)
            
            # Apply optimizations
            result = await self.apply_optimizations(plan)
            
            return {
                "optimization_id": plan["optimization_id"],
                "changes": result["changes"],
                "impact": result["impact"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Routing optimization failed: {str(e)}"
            )

    async def collect_traffic_data(self, timeframe: str) -> Dict:
        """Collect API traffic data."""
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - self._parse_timeframe(timeframe)
        
        # Query traffic data
        traffic_data = await self.traffic.find({
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }).to_list(None)
        
        return {
            "data": traffic_data,
            "start_time": start_time,
            "end_time": end_time
        }

    async def analyze_patterns(self, data: Dict) -> Dict:
        """Analyze traffic patterns using ML."""
        # Prepare features
        features = await self._extract_features(data["data"])
        
        # Detect patterns
        clusters = self.pattern_detector.fit_predict(features)
        
        # Analyze clusters
        analysis = await self._analyze_clusters(clusters, features)
        
        return {
            "analysis_id": f"analysis_{datetime.utcnow().timestamp()}",
            "details": analysis
        }

    async def _extract_features(self, traffic_data: List[Dict]) -> np.ndarray:
        """Extract features from traffic data."""
        features = []
        for entry in traffic_data:
            feature_vector = [
                entry.get("request_count", 0),
                entry.get("error_rate", 0),
                entry.get("average_latency", 0),
                entry.get("unique_users", 0),
                entry.get("bandwidth_usage", 0)
            ]
            features.append(feature_vector)
        return np.array(features)

    async def _analyze_clusters(
        self,
        clusters: np.ndarray,
        features: np.ndarray
    ) -> List[Dict]:
        """Analyze traffic clusters."""
        analysis = []
        for cluster_id in range(self.pattern_detector.n_clusters):
            cluster_features = features[clusters == cluster_id]
            analysis.append({
                "cluster_id": cluster_id,
                "size": len(cluster_features),
                "average_requests": float(cluster_features[:, 0].mean()),
                "average_errors": float(cluster_features[:, 1].mean()),
                "average_latency": float(cluster_features[:, 2].mean())
            })
        return analysis

    def _parse_timeframe(self, timeframe: str) -> timedelta:
        """Parse timeframe string into timedelta."""
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        
        if unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        elif unit == 'w':
            return timedelta(weeks=value)
        else:
            raise ValueError(f"Invalid timeframe format: {timeframe}")
