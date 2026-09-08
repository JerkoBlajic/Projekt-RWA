# =============================================================
# models/__init__.py - ORM model registry
# =============================================================
# Importing every model here guarantees they are all registered
# on Base.metadata BEFORE Alembic reads it for autogenerate.
# Every new model MUST be imported here.
# =============================================================

from core.database import Base
from models.amenity import Amenity, apartment_amenities
from models.apartment import Apartment
from models.enums import ReservationStatus, Role
from models.reservation import Reservation
from models.user import User

__all__ = [
    "Base",
    "User",
    "Apartment",
    "Reservation",
    "Amenity",
    "apartment_amenities",
    "Role",
    "ReservationStatus",
]
