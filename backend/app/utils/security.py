"""Security utilities - password hashing and JWT"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import base64
import hashlib
from jose import JWTError, jwt
from cryptography.fernet import Fernet

from app.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    if not plain_password or not hashed_password:
        return False
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# JWT token handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def _get_encryption_key() -> bytes:
    """Generate a proper Fernet encryption key from SECRET_KEY"""
    key_source = settings.ENCRYPTION_KEY or settings.SECRET_KEY
    key_hash = hashlib.sha256(key_source.encode()).digest()
    # Fernet requires a URL-safe base64-encoded 32-byte key
    return base64.urlsafe_b64encode(key_hash)


def create_fernet() -> Fernet:
    """Create Fernet instance for encryption"""
    key = _get_encryption_key()
    return Fernet(key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key"""
    try:
        f = create_fernet()
        return f.encrypt(api_key.encode()).decode()
    except Exception:
        return api_key


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key"""
    if encrypted_key == "":
        return ""
    if not encrypted_key.startswith("gAAAA"):
        return encrypted_key
    try:
        f = create_fernet()
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception:
        raise ValueError("Failed to decrypt API key")
