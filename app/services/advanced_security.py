from typing import Dict, Optional
from fastapi import HTTPException
from datetime import datetime, timedelta
import jwt
import pyotp
import qrcode
import io
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
from app.core.config import settings

class AdvancedSecurityService:
    def __init__(self, db):
        self.db = db
        self.security_logs = self.db.security_logs
        self.user_devices = self.db.user_devices
        self.api_keys = self.db.api_keys
        
        # Initialize encryption
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        self._init_rsa_keys()

    def _init_rsa_keys(self):
        """Initialize RSA keys for asymmetric encryption."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    async def generate_fingerprint_token(
        self, 
        user_id: str,
        device_info: Dict
    ) -> Dict:
        """Generate a fingerprint-based authentication token."""
        try:
            # Create device fingerprint
            fingerprint = self._create_device_fingerprint(device_info)
            
            # Store device association
            await self.user_devices.update_one(
                {"user_id": user_id, "fingerprint": fingerprint},
                {"$set": {
                    "last_used": datetime.now(),
                    "device_info": device_info
                }},
                upsert=True
            )

            # Generate token
            token = jwt.encode(
                {
                    "user_id": user_id,
                    "fingerprint": fingerprint,
                    "exp": datetime.now() + timedelta(days=30)
                },
                settings.JWT_SECRET,
                algorithm="HS256"
            )

            return {
                "token": token,
                "fingerprint": fingerprint,
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate fingerprint token: {str(e)}"
            )

    async def verify_fingerprint_token(
        self, 
        token: str,
        device_info: Dict
    ) -> bool:
        """Verify a fingerprint-based authentication token."""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=["HS256"]
            )

            # Verify fingerprint
            current_fingerprint = self._create_device_fingerprint(device_info)
            if current_fingerprint != payload["fingerprint"]:
                return False

            # Check if device is still associated
            device = await self.user_devices.find_one({
                "user_id": payload["user_id"],
                "fingerprint": current_fingerprint
            })

            return device is not None
        except jwt.ExpiredSignatureError:
            return False
        except Exception:
            return False

    async def generate_adaptive_api_key(
        self,
        user_id: str,
        permissions: Dict,
        expiry_days: int = 30
    ) -> Dict:
        """Generate an adaptive API key with dynamic permissions."""
        try:
            # Generate key and secret
            api_key = self._generate_secure_key()
            api_secret = self._generate_secure_key()

            # Hash secret for storage
            hashed_secret = self._hash_secret(api_secret)

            # Store API key
            await self.api_keys.insert_one({
                "user_id": user_id,
                "api_key": api_key,
                "hashed_secret": hashed_secret,
                "permissions": permissions,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(days=expiry_days),
                "last_rotated": datetime.now()
            })

            return {
                "api_key": api_key,
                "api_secret": api_secret,
                "permissions": permissions,
                "expires_at": (datetime.now() + timedelta(days=expiry_days)).isoformat()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate API key: {str(e)}"
            )

    async def setup_2fa(self, user_id: str) -> Dict:
        """Set up two-factor authentication for a user."""
        try:
            # Generate secret
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)

            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp.provisioning_uri(
                name=user_id,
                issuer_name="API Security"
            ))
            qr.make(fit=True)

            # Create QR code image
            img_buffer = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(img_buffer)
            qr_base64 = base64.b64encode(img_buffer.getvalue()).decode()

            # Store secret
            await self.db.users.update_one(
                {"_id": user_id},
                {
                    "$set": {
                        "2fa_secret": self.fernet.encrypt(secret.encode()).decode(),
                        "2fa_enabled": True
                    }
                }
            )

            return {
                "secret": secret,
                "qr_code": qr_base64,
                "backup_codes": self._generate_backup_codes()
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to setup 2FA: {str(e)}"
            )

    async def verify_2fa(self, user_id: str, code: str) -> bool:
        """Verify a 2FA code."""
        try:
            user = await self.db.users.find_one({"_id": user_id})
            if not user or not user.get("2fa_enabled"):
                return False

            secret = self.fernet.decrypt(
                user["2fa_secret"].encode()
            ).decode()

            totp = pyotp.TOTP(secret)
            return totp.verify(code)
        except Exception:
            return False

    def _create_device_fingerprint(self, device_info: Dict) -> str:
        """Create a unique device fingerprint."""
        fingerprint_data = f"{device_info.get('user_agent', '')}{device_info.get('platform', '')}{device_info.get('screen', '')}"
        return self._hash_data(fingerprint_data)

    def _generate_secure_key(self) -> str:
        """Generate a secure random key."""
        return base64.urlsafe_b64encode(
            jwt.utils.force_bytes(jwt.utils.force_bytes(datetime.now()) + jwt.utils.force_bytes(settings.JWT_SECRET))
        ).decode('utf-8')

    def _hash_secret(self, secret: str) -> str:
        """Hash an API secret for storage."""
        return jwt.encode(
            {"secret": secret},
            settings.JWT_SECRET,
            algorithm="HS256"
        )

    def _hash_data(self, data: str) -> str:
        """Create a hash of data."""
        return jwt.encode(
            {"data": data},
            settings.JWT_SECRET,
            algorithm="HS256"
        )

    def _generate_backup_codes(self, count: int = 8) -> List[str]:
        """Generate backup codes for 2FA."""
        return [
            ''.join(random.choices('0123456789ABCDEF', k=8))
            for _ in range(count)
        ]
