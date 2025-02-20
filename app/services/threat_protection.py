from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import numpy as np
from sklearn.ensemble import IsolationForest
import tensorflow as tf
from tensorflow import keras
import redis
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import requests
import hashlib
import jwt
from cryptography.fernet import Fernet

from app.core.config import settings

class ThreatProtectionService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.threats = self.db.threats
        self.anomalies = self.db.anomalies
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize ML models
        self.anomaly_detector = IsolationForest(contamination=0.1)
        self.threat_classifier = None
        self.load_threat_models()

    async def detect_api_intrusion(self, request_data: Dict) -> Dict:
        """
        AI-powered API intrusion detection.
        """
        try:
            # Extract features
            features = await self.extract_intrusion_features(request_data)
            
            # Run detection
            is_intrusion = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._run_intrusion_detection,
                features
            )
            
            if is_intrusion:
                await self.log_intrusion_attempt(request_data)
                
            return {
                "is_intrusion": bool(is_intrusion),
                "confidence": float(np.abs(is_intrusion)),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Intrusion detection failed: {str(e)}"
            )

    async def detect_api_anomaly(self, request_data: Dict) -> Dict:
        """
        Real-time API anomaly detection using AI.
        """
        try:
            # Extract features
            features = await self.extract_anomaly_features(request_data)
            
            # Run detection
            is_anomaly = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._run_anomaly_detection,
                features
            )
            
            if is_anomaly:
                await self.log_anomaly(request_data)
            
            return {
                "is_anomaly": bool(is_anomaly),
                "confidence": float(np.abs(is_anomaly)),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Anomaly detection failed: {str(e)}"
            )

    async def generate_dynamic_api_key(
        self,
        user_id: str,
        permissions: List[str],
        expiry_days: int = 30
    ) -> Dict:
        """
        Generate dynamic API key with encryption.
        """
        try:
            # Generate key components
            key_id = hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:8]
            secret = Fernet.generate_key().decode()
            
            # Create encrypted key
            fernet = Fernet(secret.encode())
            encrypted_data = fernet.encrypt(json.dumps({
                "user_id": user_id,
                "permissions": permissions,
                "created_at": datetime.utcnow().isoformat()
            }).encode())
            
            api_key = f"{key_id}.{encrypted_data.decode()}"
            
            # Store key information
            await self.db.api_keys.insert_one({
                "key_id": key_id,
                "user_id": user_id,
                "permissions": permissions,
                "secret_hash": hashlib.sha256(secret.encode()).hexdigest(),
                "expires_at": datetime.utcnow() + timedelta(days=expiry_days),
                "created_at": datetime.utcnow()
            })
            
            return {
                "api_key": api_key,
                "secret": secret,
                "expires_at": datetime.utcnow() + timedelta(days=expiry_days)
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API key generation failed: {str(e)}"
            )

    async def validate_api_key_signature(
        self,
        api_key: str,
        signature: str,
        request_data: Dict
    ) -> bool:
        """
        Validate API key signature for request.
        """
        try:
            key_id = api_key.split('.')[0]
            key_info = await self.db.api_keys.find_one({"key_id": key_id})
            
            if not key_info:
                return False
            
            # Verify signature
            expected_signature = self.generate_request_signature(
                request_data,
                key_info["secret_hash"]
            )
            
            return signature == expected_signature
        except Exception:
            return False

    async def check_ip_reputation(self, ip_address: str) -> Dict:
        """
        Check IP reputation and scoring.
        """
        try:
            # Check cache first
            cached = await self.redis.get(f"ip_rep:{ip_address}")
            if cached:
                return json.loads(cached)
            
            # Get reputation data
            reputation = await self.get_ip_reputation_data(ip_address)
            
            # Cache results
            await self.redis.setex(
                f"ip_rep:{ip_address}",
                300,  # 5 minutes cache
                json.dumps(reputation)
            )
            
            return reputation
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"IP reputation check failed: {str(e)}"
            )

    async def enforce_zero_trust_access(
        self,
        request_data: Dict,
        user_context: Dict
    ) -> bool:
        """
        Enforce Zero Trust API access policy.
        """
        try:
            # Verify device trust
            device_trusted = await self.verify_device_trust(
                user_context.get("device_id"),
                user_context.get("device_fingerprint")
            )
            
            # Verify network trust
            network_trusted = await self.verify_network_trust(
                request_data.get("ip_address"),
                request_data.get("location")
            )
            
            # Verify user context
            user_trusted = await self.verify_user_trust(
                user_context.get("user_id"),
                user_context.get("authentication_method")
            )
            
            return all([device_trusted, network_trusted, user_trusted])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Zero trust verification failed: {str(e)}"
            )

    async def detect_dns_threats(self, domain: str) -> Dict:
        """
        DNS filtering for malicious requests.
        """
        try:
            # Check DNS blacklists
            is_blacklisted = await self.check_dns_blacklists(domain)
            
            # Check domain reputation
            reputation = await self.get_domain_reputation(domain)
            
            # Check for DNS tunneling
            tunneling_detected = await self.detect_dns_tunneling(domain)
            
            return {
                "is_blacklisted": is_blacklisted,
                "reputation_score": reputation.get("score", 0),
                "tunneling_detected": tunneling_detected,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DNS threat detection failed: {str(e)}"
            )

    async def handle_breach_response(self, breach_data: Dict) -> Dict:
        """
        AI-powered API breach response and prevention.
        """
        try:
            # Analyze breach
            analysis = await self.analyze_breach(breach_data)
            
            # Generate response plan
            response_plan = await self.generate_breach_response(analysis)
            
            # Execute immediate actions
            await self.execute_breach_response(response_plan)
            
            return {
                "breach_analysis": analysis,
                "response_plan": response_plan,
                "status": "handled",
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Breach response failed: {str(e)}"
            )

    def load_threat_models(self):
        """
        Load ML models for threat detection.
        """
        try:
            # Load models from storage
            self.threat_classifier = keras.models.load_model("models/threat_classifier")
        except Exception:
            # Initialize new model if loading fails
            self.threat_classifier = self.initialize_threat_model()

    def initialize_threat_model(self) -> keras.Model:
        """
        Initialize a new threat detection model.
        """
        model = keras.Sequential([
            keras.layers.Dense(64, activation='relu', input_shape=(20,)),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(32, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy')
        return model

    async def extract_intrusion_features(self, request_data: Dict) -> np.ndarray:
        """
        Extract features for intrusion detection.
        """
        # Implementation would extract relevant features
        return np.array([])

    async def extract_anomaly_features(self, request_data: Dict) -> np.ndarray:
        """
        Extract features for anomaly detection.
        """
        # Implementation would extract relevant features
        return np.array([])

    def _run_intrusion_detection(self, features: np.ndarray) -> float:
        """
        Run intrusion detection model.
        """
        return self.threat_classifier.predict(features.reshape(1, -1))[0]

    def _run_anomaly_detection(self, features: np.ndarray) -> float:
        """
        Run anomaly detection model.
        """
        return self.anomaly_detector.predict(features.reshape(1, -1))[0]

    async def log_intrusion_attempt(self, request_data: Dict):
        """
        Log intrusion attempt.
        """
        await self.threats.insert_one({
            "type": "intrusion",
            "request_data": request_data,
            "created_at": datetime.utcnow()
        })

    async def log_anomaly(self, request_data: Dict):
        """
        Log detected anomaly.
        """
        await self.anomalies.insert_one({
            "request_data": request_data,
            "created_at": datetime.utcnow()
        })

    def generate_request_signature(self, request_data: Dict, secret: str) -> str:
        """
        Generate request signature.
        """
        data = json.dumps(request_data, sort_keys=True)
        return hashlib.sha256(f"{data}{secret}".encode()).hexdigest()

    async def get_ip_reputation_data(self, ip_address: str) -> Dict:
        """
        Get IP reputation data from various sources.
        """
        # Implementation would get reputation data
        return {}

    async def verify_device_trust(
        self,
        device_id: str,
        device_fingerprint: str
    ) -> bool:
        """
        Verify device trust level.
        """
        # Implementation would verify device
        return True

    async def verify_network_trust(
        self,
        ip_address: str,
        location: Dict
    ) -> bool:
        """
        Verify network trust level.
        """
        # Implementation would verify network
        return True

    async def verify_user_trust(
        self,
        user_id: str,
        auth_method: str
    ) -> bool:
        """
        Verify user trust level.
        """
        # Implementation would verify user
        return True

    async def check_dns_blacklists(self, domain: str) -> bool:
        """
        Check domain against DNS blacklists.
        """
        # Implementation would check blacklists
        return False

    async def get_domain_reputation(self, domain: str) -> Dict:
        """
        Get domain reputation data.
        """
        # Implementation would get reputation
        return {}

    async def detect_dns_tunneling(self, domain: str) -> bool:
        """
        Detect DNS tunneling attempts.
        """
        # Implementation would detect tunneling
        return False

    async def analyze_breach(self, breach_data: Dict) -> Dict:
        """
        Analyze API breach data.
        """
        # Implementation would analyze breach
        return {}

    async def generate_breach_response(self, analysis: Dict) -> Dict:
        """
        Generate breach response plan.
        """
        # Implementation would generate plan
        return {}

    async def execute_breach_response(self, response_plan: Dict):
        """
        Execute breach response plan.
        """
        # Implementation would execute plan
        pass
