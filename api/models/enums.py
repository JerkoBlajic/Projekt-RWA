# =============================================================
# enums.py - Domain enumerations
# =============================================================
# Stored as plain strings in the database (simple, portable,
# no native PG enum migrations). Validated in the schema layer.
# =============================================================

from enum import Enum


class Role(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


# Statuses that block a date range from being re-booked.
ACTIVE_RESERVATION_STATUSES = (
    ReservationStatus.PENDING.value,
    ReservationStatus.APPROVED.value,
)
