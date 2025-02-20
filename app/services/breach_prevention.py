from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import json
import asyncio
from datetime import datetime
import openai
import numpy as np
from sklearn.ensemble import IsolationForest
import tensorflow as tf
from transformers import AutoTokenizer, AutoModel
import requests
import logging
from prometheus_client import Counter, Histogram
import aiohttp
from app.core.config import settings

class BreachPreventionService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.breaches = self.db.breaches
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        
        # Initialize ML models
        self.anomaly_detector = IsolationForest(contamination=0.1)
        self.threat_classifier = AutoModel.from_pretrained("microsoft/codebert-base")
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        
        # Initialize metrics
        self.breach_attempts = Counter(
            'breach_attempts_total',
            'Total number of detected breach attempts'
        )
        self.prevention_actions = Counter(
            'prevention_actions_total',
            'Total number of prevention actions taken'
        )

    async def detect_breach_attempts(
        self,
        request_data: Dict
    ) -> Dict:
        """
        Detect potential API breach attempts.
        """
        try:
            # Analyze request
            analysis = await self.analyze_request(request_data)
            
            # Detect anomalies
            anomalies = await self.detect_anomalies(analysis)
            
            # Generate alerts
            alerts = await self.generate_alerts(anomalies)
            
            return {
                "detection_id": analysis["detection_id"],
                "anomalies": anomalies,
                "alerts": alerts,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Breach detection failed: {str(e)}"
            )

    async def prevent_breach(
        self,
        threat_data: Dict
    ) -> Dict:
        """
        Take action to prevent detected breaches.
        """
        try:
            # Analyze threat
            analysis = await self.analyze_threat(threat_data)
            
            # Generate response
            response = await self.generate_response(analysis)
            
            # Execute prevention
            prevention = await self.execute_prevention(response)
            
            return {
                "prevention_id": prevention["prevention_id"],
                "actions": prevention["actions"],
                "status": prevention["status"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Breach prevention failed: {str(e)}"
            )

    async def analyze_breach_patterns(
        self,
        timeframe: str = "24h"
    ) -> Dict:
        """
        Analyze breach attempt patterns.
        """
        try:
            # Collect data
            data = await self.collect_breach_data(timeframe)
            
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
                detail=f"Pattern analysis failed: {str(e)}"
            )

    async def update_prevention_rules(
        self,
        new_patterns: Dict
    ) -> Dict:
        """
        Update breach prevention rules based on new patterns.
        """
        try:
            # Validate patterns
            validation = await self.validate_patterns(new_patterns)
            
            # Generate rules
            rules = await self.generate_rules(validation)
            
            # Apply rules
            application = await self.apply_rules(rules)
            
            return {
                "update_id": rules["update_id"],
                "rules": rules["details"],
                "status": application["status"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rule update failed: {str(e)}"
            )

    async def generate_breach_report(
        self,
        report_config: Dict
    ) -> Dict:
        """
        Generate comprehensive breach analysis report.
        """
        try:
            # Collect data
            data = await self.collect_report_data(report_config)
            
            # Generate analysis
            analysis = await self.analyze_report_data(data)
            
            # Generate recommendations
            recommendations = await self.generate_recommendations(analysis)
            
            return {
                "report_id": data["report_id"],
                "analysis": analysis,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {str(e)}"
            )

    async def analyze_request(self, request_data: Dict) -> Dict:
        """Analyze API request for potential threats."""
        # Extract features
        features = {
            "ip": request_data.get("ip"),
            "method": request_data.get("method"),
            "path": request_data.get("path"),
            "headers": request_data.get("headers", {}),
            "body": request_data.get("body", {})
        }
        
        # Generate embeddings
        embeddings = await self._generate_embeddings(features)
        
        # Detect anomalies
        anomaly_score = self.anomaly_detector.predict([embeddings])[0]
        
        return {
            "detection_id": f"det_{datetime.utcnow().timestamp()}",
            "features": features,
            "anomaly_score": float(anomaly_score)
        }

    async def _generate_embeddings(self, features: Dict) -> np.ndarray:
        """Generate embeddings for request features."""
        # Convert features to text
        text = json.dumps(features)
        
        # Generate embeddings using CodeBERT
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        outputs = self.threat_classifier(**inputs)
        
        return outputs.last_hidden_state.mean(dim=1).detach().numpy()[0]

    async def analyze_threat(self, threat_data: Dict) -> Dict:
        """Analyze detected threat."""
        # Extract threat details
        threat_type = threat_data.get("type")
        severity = threat_data.get("severity")
        source = threat_data.get("source")
        
        # Generate threat score
        threat_score = await self._calculate_threat_score(
            threat_type,
            severity,
            source
        )
        
        return {
            "threat_id": f"threat_{datetime.utcnow().timestamp()}",
            "type": threat_type,
            "severity": severity,
            "source": source,
            "score": threat_score
        }

    async def _calculate_threat_score(
        self,
        threat_type: str,
        severity: str,
        source: Dict
    ) -> float:
        """Calculate threat score based on various factors."""
        # Base scores
        type_scores = {
            "sql_injection": 0.9,
            "xss": 0.8,
            "ddos": 0.7,
            "brute_force": 0.6
        }
        
        severity_scores = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        
        # Calculate score
        base_score = type_scores.get(threat_type, 0.5)
        severity_multiplier = severity_scores.get(severity, 0.5)
        
        return base_score * severity_multiplier
