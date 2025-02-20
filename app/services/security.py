from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import jwt
import hashlib
import hmac
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import ipaddress
import geoip2.database
import redis
import json

from app.core.config import settings

class SecurityService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.MONGODB_URL)[settings.MONGODB_DATABASE]
        self.security_logs = self.db.security_logs
        self.blocked_ips = self.db.blocked_ips
        self.api_keys = self.db.api_keys
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        
        # Initialize GeoIP database
        self.geoip_reader = geoip2.database.Reader('path/to/GeoLite2-City.mmdb')

    async def validate_jwt_fingerprint(self, token: str, fingerprint: str) -> bool:
        """
        Validate JWT with browser fingerprint.
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            stored_fingerprint = payload.get("fingerprint")
            return hmac.compare_digest(stored_fingerprint, fingerprint)
        except jwt.JWTError:
            return False

    async def create_tamper_proof_jwt(
        self,
        data: Dict,
        fingerprint: str,
        expiry: timedelta
    ) -> str:
        """
        Create a tamper-proof JWT with additional security measures.
        """
        timestamp = datetime.utcnow()
        expiry_time = timestamp + expiry
        
        # Add security-related claims
        payload = {
            **data,
            "fingerprint": fingerprint,
            "iat": timestamp,
            "exp": expiry_time,
            "jti": secrets.token_hex(32)  # Unique token ID
        }
        
        # Sign token with additional headers
        token = jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
            headers={
                "typ": "JWT",
                "alg": settings.JWT_ALGORITHM,
                "kid": settings.KEY_ID
            }
        )
        
        # Store token metadata for additional validation
        await self.redis.setex(
            f"token:{payload['jti']}",
            int(expiry.total_seconds()),
            json.dumps({
                "fingerprint": fingerprint,
                "user_id": data.get("sub"),
                "created_at": timestamp.isoformat()
            })
        )
        
        return token

    async def verify_request_signature(
        self,
        signature: str,
        payload: str,
        api_key: str
    ) -> bool:
        """
        Verify request signature using HMAC.
        """
        try:
            api_key_data = await self.api_keys.find_one({"key": api_key})
            if not api_key_data:
                return False
            
            expected_signature = hmac.new(
                api_key_data["secret"].encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception:
            return False

    async def prevent_replay_attack(self, nonce: str, timestamp: str) -> bool:
        """
        Prevent API replay attacks.
        """
        current_time = datetime.utcnow()
        request_time = datetime.fromisoformat(timestamp)
        
        # Check if request is within acceptable time window (e.g., 5 minutes)
        if current_time - request_time > timedelta(minutes=5):
            return False
        
        # Check if nonce has been used
        nonce_key = f"nonce:{nonce}"
        if await self.redis.exists(nonce_key):
            return False
        
        # Store nonce with expiration
        await self.redis.setex(nonce_key, 300, "1")  # 5 minutes expiry
        return True

    async def encrypt_data(self, data: str) -> str:
        """
        Encrypt data using Fernet (symmetric encryption).
        """
        return self.fernet.encrypt(data.encode()).decode()

    async def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt Fernet-encrypted data.
        """
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid encrypted data"
            )

    async def generate_api_key_pair(self) -> Dict[str, str]:
        """
        Generate a new API key and secret pair.
        """
        api_key = secrets.token_urlsafe(32)
        api_secret = secrets.token_urlsafe(64)
        
        # Hash the secret for storage
        secret_hash = hashlib.sha256(api_secret.encode()).hexdigest()
        
        await self.api_keys.insert_one({
            "key": api_key,
            "secret_hash": secret_hash,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "is_active": True
        })
        
        return {
            "api_key": api_key,
            "api_secret": api_secret  # Only returned once during creation
        }

    async def check_ip_reputation(self, ip_address: str) -> Dict:
        """
        Check IP reputation and apply security measures.
        """
        try:
            # Check if IP is blocked
            if await self.blocked_ips.find_one({"ip": ip_address}):
                return {"status": "blocked", "risk_score": 1.0}
            
            # Get IP geo-location
            geo_data = self.geoip_reader.city(ip_address)
            
            # Check recent security events from this IP
            recent_events = await self.security_logs.count_documents({
                "ip_address": ip_address,
                "timestamp": {
                    "$gte": datetime.utcnow() - timedelta(hours=24)
                },
                "event_type": {"$in": ["failed_login", "api_abuse", "attack_attempt"]}
            })
            
            # Calculate risk score (0.0 to 1.0)
            risk_score = min(1.0, recent_events / 100)
            
            return {
                "status": "allowed" if risk_score < 0.7 else "suspicious",
                "risk_score": risk_score,
                "country": geo_data.country.name,
                "city": geo_data.city.name,
                "recent_events": recent_events
            }
        except Exception as e:
            # Log error and return conservative risk assessment
            await self.log_security_event(
                "ip_check_error",
                {"ip": ip_address, "error": str(e)}
            )
            return {"status": "suspicious", "risk_score": 0.7}

    async def validate_zero_trust_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        context: Dict
    ) -> bool:
        """
        Validate access using Zero Trust principles.
        """
        try:
            # Get user's current security context
            user_context = await self.get_user_security_context(user_id)
            
            # Verify device trust level
            if not await self.verify_device_trust(context.get("device_id")):
                return False
            
            # Check network security level
            if not await self.verify_network_security(context.get("ip_address")):
                return False
            
            # Verify user's authentication strength
            if not await self.verify_auth_strength(user_context):
                return False
            
            # Check resource-specific permissions
            if not await self.check_resource_permissions(user_id, resource, action):
                return False
            
            # Log access attempt
            await self.log_security_event(
                "zero_trust_access",
                {
                    "user_id": user_id,
                    "resource": resource,
                    "action": action,
                    "context": context
                }
            )
            
            return True
        except Exception as e:
            await self.log_security_event(
                "zero_trust_error",
                {
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            return False

    async def log_security_event(self, event_type: str, data: Dict) -> None:
        """
        Log security-related events.
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow()
        }
        
        await self.security_logs.insert_one(event)

    async def get_security_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get security events for analysis.
        """
        query = {
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time
            }
        }
        
        if event_type:
            query["type"] = event_type
        
        events = await self.security_logs.find(query).to_list(None)
        return [{**event, "id": str(event["_id"])} for event in events]

    async def verify_device_trust(self, device_id: str) -> bool:
        """
        Verify device trust level.
        """
        # Implementation would check device security status
        return True

    async def verify_network_security(self, ip_address: str) -> bool:
        """
        Verify network security level.
        """
        # Implementation would check network security
        return True

    async def verify_auth_strength(self, user_context: Dict) -> bool:
        """
        Verify authentication strength.
        """
        # Implementation would verify auth strength
        return True

    async def check_resource_permissions(
        self,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check resource-specific permissions.
        """
        # Implementation would check permissions
        return True

    async def get_user_security_context(self, user_id: str) -> Dict:
        """
        Get user's current security context.
        """
        # Implementation would get security context
        return {}
