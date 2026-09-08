# =============================================================
# user.py - User ORM model
# =============================================================
# A user can act as an apartment owner (users 1:N apartments)
# and/or as a guest who books apartments (users 1:N reservations).
#
#   role           - "USER" or "ADMIN"
#   password_hash  - bcrypt hash, NEVER plain text
# =============================================================

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.enums import Role

if TYPE_CHECKING:
    from models.apartment import Apartment
    from models.reservation import Reservation


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=Role.USER.value)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    apartments: Mapped[list[Apartment]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    reservations: Mapped[list[Reservation]] = relationship(
        back_populates="guest", cascade="all, delete-orphan"
    )
