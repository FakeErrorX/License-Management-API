from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import ipaddress
import geoip2.database
from geoip2.errors import AddressNotFoundError
import numpy as np
from sklearn.ensemble import IsolationForest

from app.core.config import settings

class RateLimiterService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.rate_limits = self.db.rate_limits
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize ML model for fraud detection
        self.fraud_detector = IsolationForest(
            contamination=0.1,
            random_state=42
        )
        
        # Initialize GeoIP database
        self.geoip_reader = geoip2.database.Reader('path/to/GeoLite2-City.mmdb')

    async def check_rate_limit(self, request_data: Dict) -> Dict:
        """
        Check if request exceeds rate limits.
        """
        try:
            # Get rate limit rules
            rules = await self.get_rate_limit_rules(request_data)
            
            # Check limits
            result = await self.check_limits(request_data, rules)
            
            # Update counters
            await self.update_rate_counters(request_data)
            
            return {
                "allowed": result["allowed"],
                "remaining": result["remaining"],
                "reset_at": result["reset_at"],
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rate limit check failed: {str(e)}"
            )

    async def detect_abuse(self, request_data: Dict) -> Dict:
        """
        Detect potential API abuse.
        """
        try:
            # Check fraud indicators
            fraud_score = await self.check_fraud_indicators(request_data)
            
            # Check IP reputation
            ip_score = await self.check_ip_reputation(request_data["ip"])
            
            # Check device reputation
            device_score = await self.check_device_reputation(
                request_data.get("device_id")
            )
            
            return {
                "abuse_detected": fraud_score > 0.7,
                "risk_score": fraud_score,
                "ip_score": ip_score,
                "device_score": device_score,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Abuse detection failed: {str(e)}"
            )

    async def update_rate_limits(
        self,
        user_id: str,
        new_limits: Dict
    ) -> Dict:
        """
        Update rate limits for a user.
        """
        try:
            # Validate new limits
            validated_limits = await self.validate_rate_limits(new_limits)
            
            # Update limits
            await self.rate_limits.update_one(
                {"user_id": user_id},
                {"$set": validated_limits},
                upsert=True
            )
            
            return {
                "user_id": user_id,
                "limits": validated_limits,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rate limit update failed: {str(e)}"
            )

    async def get_geo_limits(self, country_code: str) -> Dict:
        """
        Get geo-based rate limits.
        """
        try:
            # Get country limits
            limits = await self.rate_limits.find_one({"country": country_code})
            
            if not limits:
                # Use default limits
                limits = await self.get_default_geo_limits()
            
            return {
                "country": country_code,
                "limits": limits,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Geo limits retrieval failed: {str(e)}"
            )

    async def check_ddos_attack(self, request_data: Dict) -> Dict:
        """
        Check for potential DDoS attack.
        """
        try:
            # Analyze traffic pattern
            pattern = await self.analyze_traffic_pattern(request_data)
            
            # Check for attack indicators
            indicators = await self.check_ddos_indicators(pattern)
            
            # Generate mitigation actions
            actions = await self.generate_ddos_actions(indicators)
            
            return {
                "attack_detected": indicators["is_attack"],
                "confidence": indicators["confidence"],
                "recommended_actions": actions,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"DDoS check failed: {str(e)}"
            )

    async def manage_blacklist(
        self,
        action: str,
        target: Dict
    ) -> Dict:
        """
        Manage API blacklist.
        """
        try:
            if action == "add":
                result = await self.add_to_blacklist(target)
            elif action == "remove":
                result = await self.remove_from_blacklist(target)
            else:
                raise ValueError("Invalid action")
            
            return {
                "action": action,
                "target": target,
                "result": result,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Blacklist operation failed: {str(e)}"
            )

    async def adjust_dynamic_limits(
        self,
        metrics: Dict
    ) -> Dict:
        """
        Dynamically adjust rate limits based on metrics.
        """
        try:
            # Analyze current load
            load = await self.analyze_system_load(metrics)
            
            # Calculate new limits
            new_limits = await self.calculate_dynamic_limits(load)
            
            # Apply new limits
            await self.apply_dynamic_limits(new_limits)
            
            return {
                "new_limits": new_limits,
                "load_factors": load,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Dynamic limit adjustment failed: {str(e)}"
            )

    async def check_fraud_indicators(self, request_data: Dict) -> float:
        """
        Check for fraud indicators using ML.
        """
        try:
            # Extract features
            features = await self.extract_fraud_features(request_data)
            
            # Run prediction
            prediction = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.fraud_detector.predict,
                features.reshape(1, -1)
            )
            
            return float(prediction[0])
        except Exception:
            return 0.0

    async def check_ip_reputation(self, ip: str) -> float:
        """
        Check IP reputation score.
        """
        try:
            # Get IP info
            ip_info = await self.get_ip_info(ip)
            
            # Calculate reputation score
            score = await self.calculate_ip_score(ip_info)
            
            return score
        except Exception:
            return 0.0

    async def check_device_reputation(self, device_id: Optional[str]) -> float:
        """
        Check device reputation score.
        """
        try:
            if not device_id:
                return 0.0
            
            # Get device history
            history = await self.get_device_history(device_id)
            
            # Calculate reputation score
            score = await self.calculate_device_score(history)
            
            return score
        except Exception:
            return 0.0

    async def analyze_traffic_pattern(self, request_data: Dict) -> Dict:
        """
        Analyze traffic pattern for DDoS detection.
        """
        try:
            # Get recent traffic
            traffic = await self.get_recent_traffic()
            
            # Analyze pattern
            pattern = await self.analyze_pattern(traffic)
            
            return pattern
        except Exception:
            return {}

    async def check_ddos_indicators(self, pattern: Dict) -> Dict:
        """
        Check for DDoS attack indicators.
        """
        try:
            indicators = {
                "request_rate": pattern.get("request_rate", 0),
                "unique_ips": pattern.get("unique_ips", 0),
                "error_rate": pattern.get("error_rate", 0)
            }
            
            is_attack = (
                indicators["request_rate"] > settings.DDOS_REQUEST_THRESHOLD and
                indicators["error_rate"] > settings.DDOS_ERROR_THRESHOLD
            )
            
            return {
                "is_attack": is_attack,
                "confidence": 0.9 if is_attack else 0.1,
                "indicators": indicators
            }
        except Exception:
            return {"is_attack": False, "confidence": 0.0, "indicators": {}}

    async def generate_ddos_actions(self, indicators: Dict) -> List[Dict]:
        """
        Generate DDoS mitigation actions.
        """
        try:
            actions = []
            if indicators["is_attack"]:
                actions.extend([
                    {
                        "type": "block",
                        "target": "ip_range",
                        "priority": "high"
                    },
                    {
                        "type": "rate_limit",
                        "target": "global",
                        "priority": "high"
                    }
                ])
            return actions
        except Exception:
            return []
