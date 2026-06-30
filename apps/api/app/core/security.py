import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import AppError

PASSWORD_PREFIX = "bcrypt_sha256$"


def hash_password(password: str) -> str:
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    hashed = bcrypt.hashpw(digest, bcrypt.gensalt(rounds=12)).decode("utf-8")
    return f"{PASSWORD_PREFIX}{hashed}"


def verify_password(password: str, hashed_password: str) -> bool:
    if not hashed_password.startswith(PASSWORD_PREFIX):
        return False
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    stored = hashed_password.removeprefix(PASSWORD_PREFIX).encode("utf-8")
    return bcrypt.checkpw(digest, stored)


def create_access_token(subject: str, claims: dict[str, Any] | None = None) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    if claims:
        payload.update(claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise AppError("Invalid or expired token.", "INVALID_TOKEN", 401) from exc
    if not payload.get("sub"):
        raise AppError("Invalid token subject.", "INVALID_TOKEN", 401)
    return payload
