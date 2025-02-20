from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64
import hashlib
import hmac
import pyotp
import qrcode
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/{settings.API_VERSION}/auth/login")

class SecurityManager:
    def __init__(self):
        self.encryption_key = settings.ENCRYPTION_KEY.encode()
        self.api_key_salt = settings.API_KEY_SALT.encode()

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def generate_api_key(self) -> tuple[str, str]:
        api_key = base64.b64encode(get_random_bytes(32)).decode('utf-8')
        api_key_hash = self.hash_api_key(api_key)
        return api_key, api_key_hash

    def hash_api_key(self, api_key: str) -> str:
        return hmac.new(self.api_key_salt, api_key.encode(), hashlib.sha256).hexdigest()

    def verify_api_key(self, api_key: str, stored_hash: str) -> bool:
        return hmac.compare_digest(self.hash_api_key(api_key), stored_hash)

    def encrypt_data(self, data: str) -> str:
        cipher = AES.new(self.encryption_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        nonce = cipher.nonce
        encrypted_data = base64.b64encode(nonce + tag + ciphertext).decode('utf-8')
        return encrypted_data

    def decrypt_data(self, encrypted_data: str) -> str:
        try:
            data = base64.b64decode(encrypted_data.encode('utf-8'))
            nonce = data[:16]
            tag = data[16:32]
            ciphertext = data[32:]
            cipher = AES.new(self.encryption_key, AES.MODE_GCM, nonce=nonce)
            decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
            return decrypted_data.decode('utf-8')
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Decryption failed"
            )

    def generate_2fa_secret(self) -> str:
        return pyotp.random_base32()

    def verify_2fa_token(self, secret: str, token: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(token)

    def generate_2fa_qr(self, secret: str, email: str) -> bytes:
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(email, issuer_name=settings.PROJECT_NAME)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        return img.get_image()

async def setup_security(app: Any) -> None:
    app.state.security = SecurityManager()
