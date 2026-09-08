# =============================================================
# reservation.py - Pydantic schemas for the Reservation entity
# =============================================================
# Rule 1 (check_out > check_in) is enforced here as a schema
# validator -> the API answers 422 for a bad date range.
# Rules 2/3/4 depend on other rows and live in the service layer.
# =============================================================

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.enums import ReservationStatus
from schemas.user import UserResponse


class ReservationCreate(BaseModel):
    check_in: date
    check_out: date
    guests_count: int = Field(gt=0, le=100)

    @model_validator(mode="after")
    def check_dates(self) -> "ReservationCreate":
        if self.check_out <= self.check_in:
            raise ValueError("check_out must be later than check_in")
        if self.check_in < date.today():
            raise ValueError("check_in cannot be in the past")
        return self


class ReservationUpdate(BaseModel):
    """Guest edits a still-PENDING reservation."""

    check_in: date | None = None
    check_out: date | None = None
    guests_count: int | None = Field(default=None, gt=0, le=100)

    @model_validator(mode="after")
    def check_dates(self) -> "ReservationUpdate":
        if (
            self.check_in is not None
            and self.check_out is not None
            and self.check_out <= self.check_in
        ):
            raise ValueError("check_out must be later than check_in")
        return self


class BusyRange(BaseModel):
    """A blocked date span (guest identity intentionally omitted)."""

    check_in: date
    check_out: date
    status: ReservationStatus

    model_config = ConfigDict(from_attributes=True)


class ApartmentBrief(BaseModel):
    id: int
    title: str
    city: str
    price_per_night: float
    max_guests: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class GuestBrief(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class ReservationResponse(BaseModel):
    id: int
    apartment_id: int
    guest_id: int
    check_in: date
    check_out: date
    guests_count: int
    status: ReservationStatus
    created_at: datetime | None = None
    apartment: ApartmentBrief | None = None
    guest: GuestBrief | None = None

    model_config = ConfigDict(from_attributes=True)
