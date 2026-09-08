# =============================================================
# jwt.py - Create and decode JWT access / refresh tokens
# =============================================================
# access token  : short-lived (default 15 min), used for protected endpoints
# refresh token : long-lived  (default 7 days), used to mint a new access token
#
# Claims:
#   sub   - user id (string, per JWT convention)
#   role  - "USER" or "ADMIN" (access token only)
#   type  - "access" or "refresh"
#   exp   - expiry
#   iss   - issuer
# =============================================================

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from core.config import settings

ALGORITHM = "HS256"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "exp": _now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iss": settings.JWT_ISSUER,
        "exp": _now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode + validate a token. Raises jose.JWTError on any problem."""
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM],
        issuer=settings.JWT_ISSUER,
    )


__all__ = ["create_access_token", "create_refresh_token", "decode_token", "JWTError"]
