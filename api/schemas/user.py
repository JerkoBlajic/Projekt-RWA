# =============================================================
# user.py - Pydantic schemas for the User entity
# =============================================================

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.enums import Role


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: Role
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    """PATCH /admin/users/{id} - admin changes a user's role."""

    role: Role
