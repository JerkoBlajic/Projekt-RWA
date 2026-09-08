# =============================================================
# auth_service.py - Authentication business logic
# =============================================================
# This layer knows nothing about HTTP. It returns domain objects
# or raises AppError.
# =============================================================

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from core.jwt import create_access_token, create_refresh_token, decode_token
from core.security import hash_password, verify_password
from models.enums import Role
from models.user import User
from repositories import user_repo
from schemas.auth import RegisterRequest


async def register_user(db: AsyncSession, body: RegisterRequest) -> User:
    if await user_repo.get_by_username(db, body.username):
        raise AppError("username_taken", "Username is already taken", 409)
    if await user_repo.get_by_email(db, body.email):
        raise AppError("email_taken", "Email is already registered", 409)

    user = User(
        username=body.username,
        email=str(body.email).lower(),
        password_hash=hash_password(body.password),
        role=Role.USER.value,
    )
    return await user_repo.create(db, user)


async def authenticate(db: AsyncSession, username: str, password: str) -> User:
    """Same error for unknown user and wrong password (no enumeration)."""
    user = await user_repo.get_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise AppError("invalid_credentials", "Invalid username or password", 401)
    return user


def issue_tokens(user: User) -> tuple[str, str]:
    return create_access_token(user.id, user.role), create_refresh_token(user.id)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise AppError("invalid_token", "Refresh token is invalid or expired", 401)

    if payload.get("type") != "refresh":
        raise AppError("invalid_token", "Token is not a refresh token", 401)

    user = await user_repo.get_by_id(db, int(payload["sub"]))
    if not user:
        raise AppError("invalid_token", "User no longer exists", 401)

    return issue_tokens(user)
