import base64
import hashlib
from datetime import UTC, datetime
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.errors import AppError


def encrypt_oauth_token(token: str) -> dict[str, Any]:
    if not token:
        raise AppError("OAuth token cannot be empty.", "OAUTH_TOKEN_INVALID", 400)
    ciphertext = _fernet().encrypt(token.encode("utf-8")).decode("utf-8")
    return {
        "version": 1,
        "algorithm": "fernet",
        "ciphertext": ciphertext,
        "key_version": settings.oauth_token_encryption_key_version,
        "encrypted_at": datetime.now(UTC).isoformat(),
    }


def decrypt_oauth_token(envelope: dict[str, Any]) -> str:
    try:
        ciphertext = envelope["ciphertext"]
        if not isinstance(ciphertext, str):
            raise KeyError("ciphertext")
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except (InvalidToken, KeyError, TypeError, UnicodeDecodeError) as exc:
        raise AppError("Could not decrypt OAuth token.", "OAUTH_TOKEN_DECRYPT_FAILED", 500) from exc


def _fernet() -> Fernet:
    return Fernet(_get_key())


def _get_key() -> bytes:
    raw_key = settings.oauth_token_encryption_key
    if raw_key:
        return _normalize_key(raw_key)
    if settings.env == "production":
        raise AppError(
            "OAuth token encryption key is not configured.",
            "OAUTH_TOKEN_ENCRYPTION_NOT_CONFIGURED",
            503,
        )
    return _derive_key(settings.jwt_secret)


def _normalize_key(raw_key: str) -> bytes:
    candidate = raw_key.encode("utf-8")
    try:
        Fernet(candidate)
        return candidate
    except (ValueError, TypeError):
        return _derive_key(raw_key)


def _derive_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)
