# =============================================================
# deps.py - Shared FastAPI dependencies
# =============================================================
#   get_db               - one DB session per request
#   get_current_user      - decode JWT -> load User (401 on failure)
#   get_current_user_optional - same, but returns None instead of 401
#   require_admin         - 403 unless the user's role is ADMIN
# =============================================================

from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.errors import AppError
from core.jwt import JWTError, decode_token
from models.enums import Role
from models.user import User
from repositories import user_repo

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session; commit on success, rollback on error, always close."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _user_from_credentials(
    credentials: HTTPAuthorizationCredentials | None, db: AsyncSession
) -> User:
    if credentials is None:
        raise AppError("unauthorized", "Authentication token missing", 401)
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise AppError("unauthorized", "Token is invalid or has expired", 401)
    if payload.get("type") != "access":
        raise AppError("unauthorized", "Token is not an access token", 401)

    user = await user_repo.get_by_id(db, int(payload["sub"]))
    if user is None:
        raise AppError("unauthorized", "User no longer exists", 401)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    return await _user_from_credentials(credentials, db)


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        return await _user_from_credentials(credentials, db)
    except AppError:
        return None


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != Role.ADMIN.value:
        raise AppError("forbidden", "Administrator privileges required", 403)
    return current_user
