"""JWT token generation and validation utilities."""

import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from fastapi import HTTPException, status

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token.

    Args:
        data: Dictionary of claims to encode in the token (e.g., {"sub": "1", "role": "doctor"})
        expires_delta: Optional custom expiration time. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES

    Returns:
        Encoded JWT token string

    Example:
        >>> token = create_access_token({"sub": "1", "username": "dr_smith", "role": "doctor"})
        >>> print(token)
        'eyJhbGci...'
    """
    to_encode = data.copy()

    now = time.time()
    if expires_delta:
        expire = now + expires_delta.total_seconds()
    else:
        expire = now + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    to_encode.update({"exp": int(expire), "iat": int(now), "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a new JWT refresh token with longer expiration.

    Args:
        data: Dictionary of claims to encode in the token

    Returns:
        Encoded JWT refresh token string
    """
    expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(data, expires_delta)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary of decoded token claims

    Raises:
        HTTPException: 401 if token is invalid, expired, or malformed

    Example:
        >>> token = create_access_token({"sub": "1", "role": "doctor"})
        >>> payload = decode_token(token)
        >>> print(payload["sub"])
        '1'
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


def get_token_expires_in(token: str) -> int:
    """Get the remaining time in seconds until token expiration.

    Args:
        token: JWT token string

    Returns:
        Number of seconds until expiration (0 if expired)
    """
    try:
        payload = decode_token(token)
        exp_timestamp = payload.get("exp")

        if not exp_timestamp:
            return 0

        expires_at = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()

        if expires_at < now:
            return 0

        delta = expires_at - now
        return int(delta.total_seconds())
    except HTTPException:
        return 0
