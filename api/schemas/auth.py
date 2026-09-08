# =============================================================
# auth.py - Pydantic schemas for authentication
# =============================================================

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from schemas.user import UserResponse

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_charset(cls, v: str) -> str:
        if not _USERNAME_RE.match(v):
            raise ValueError(
                "username may contain only letters, digits, '.', '_' and '-'"
            )
        return v


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse
