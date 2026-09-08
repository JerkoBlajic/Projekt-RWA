# =============================================================
# reservation.py - Reservation ORM model
# =============================================================
# Relationships:
#   apartments 1 -> N reservations
#   users      1 -> N reservations   (guest_id)
#
# status lifecycle (enforced in the service layer):
#   PENDING -> APPROVED | REJECTED | CANCELLED
#   APPROVED -> CANCELLED | COMPLETED
# =============================================================

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.enums import ReservationStatus

if TYPE_CHECKING:
    from models.apartment import Apartment
    from models.user import User


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    apartment_id: Mapped[int] = mapped_column(
        ForeignKey("apartments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    guest_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    check_in: Mapped[date] = mapped_column(Date, nullable=False)
    check_out: Mapped[date] = mapped_column(Date, nullable=False)
    guests_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ReservationStatus.PENDING.value
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    apartment: Mapped[Apartment] = relationship(back_populates="reservations")
    guest: Mapped[User] = relationship(back_populates="reservations")
