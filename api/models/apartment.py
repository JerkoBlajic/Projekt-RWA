# =============================================================
# apartment.py - Apartment ORM model
# =============================================================
# Relationships:
#   users      1 -> N apartments   (owner_id)
#   apartments 1 -> N reservations
#   apartments N -> M amenities     (apartment_amenities)
# =============================================================

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from models.amenity import apartment_amenities

if TYPE_CHECKING:
    from models.amenity import Amenity
    from models.reservation import Reservation
    from models.user import User


class Apartment(Base):
    __tablename__ = "apartments"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    # Either an external URL or a base64 data URI (uploaded from the browser),
    # hence Text rather than a short String.
    image: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    price_per_night: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False)
    bedrooms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bathrooms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    area_sqm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped[User] = relationship(back_populates="apartments")
    reservations: Mapped[list[Reservation]] = relationship(
        back_populates="apartment", cascade="all, delete-orphan"
    )
    amenities: Mapped[list[Amenity]] = relationship(
        secondary=apartment_amenities, back_populates="apartments"
    )
