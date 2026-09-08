# =============================================================
# amenity.py - Amenity model + apartment_amenities join table
# =============================================================
# apartments M:N amenities. The association table has no extra
# columns, so a Core Table is enough (no ORM model needed).
# =============================================================

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.apartment import Apartment

apartment_amenities = Table(
    "apartment_amenities",
    Base.metadata,
    Column(
        "apartment_id",
        Integer,
        ForeignKey("apartments.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "amenity_id",
        Integer,
        ForeignKey("amenities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Amenity(Base):
    __tablename__ = "amenities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    apartments: Mapped[list[Apartment]] = relationship(
        secondary=apartment_amenities, back_populates="amenities"
    )
