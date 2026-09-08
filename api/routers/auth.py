# =============================================================
# auth.py - Authentication endpoints
# =============================================================
#   POST /auth/register
#   POST /auth/login
#   POST /auth/refresh
#   GET  /auth/me
# =============================================================

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.user import User
from schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from schemas.user import UserResponse
from services import auth_service

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, body)
    access, refresh = auth_service.issue_tokens(user)
    return RegisterResponse(
        user=UserResponse.model_validate(user),
        tokens=TokenResponse(access_token=access, refresh_token=refresh),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate(db, body.username, body.password)
    access, refresh = auth_service.issue_tokens(user)
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    access, refresh_tok = await auth_service.refresh_tokens(db, body.refresh_token)
    return TokenResponse(access_token=access, refresh_token=refresh_tok)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
