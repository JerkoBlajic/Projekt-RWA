# =============================================================
# reservation_service.py - Reservation business logic
# =============================================================
# Business rules (spec section 9) - ALL enforced here, never in
# the router:
#   Rule 1  check_out > check_in            (also guarded in schema -> 422)
#   Rule 2  guests_count <= apartment.max_guests   -> 422
#   Rule 3  no overlap with an active reservation  -> 409
#   Rule 4  status workflow:
#             owner:  PENDING  -> APPROVED | REJECTED
#             guest:  PENDING  -> CANCELLED
#             guest:  APPROVED -> CANCELLED
#             owner:  APPROVED -> COMPLETED
#           any other transition -> 409
# =============================================================

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.enums import ReservationStatus, Role
from models.reservation import Reservation
from models.user import User
from repositories import apartment_repo, reservation_repo
from schemas.reservation import ReservationCreate, ReservationUpdate

S = ReservationStatus

# (from_status, to_status) -> role relative to the reservation: "owner" | "guest"
_ALLOWED_TRANSITIONS: dict[tuple[str, str], str] = {
    (S.PENDING.value, S.APPROVED.value): "owner",
    (S.PENDING.value, S.REJECTED.value): "owner",
    (S.APPROVED.value, S.COMPLETED.value): "owner",
    (S.PENDING.value, S.CANCELLED.value): "guest",
    (S.APPROVED.value, S.CANCELLED.value): "guest",
}


# ---- read -------------------------------------------------------

async def _get_or_404(db: AsyncSession, reservation_id: int) -> Reservation:
    reservation = await reservation_repo.get_by_id(db, reservation_id)
    if reservation is None:
        raise AppError("not_found", "Reservation not found", 404)
    return reservation


def _relation(reservation: Reservation, user: User) -> str | None:
    """How is this user related to the reservation?"""
    if user.role == Role.ADMIN.value:
        return "admin"
    if reservation.guest_id == user.id:
        return "guest"
    if reservation.apartment.owner_id == user.id:
        return "owner"
    return None


def _assert_visible(reservation: Reservation, user: User) -> None:
    if _relation(reservation, user) is None:
        raise AppError("forbidden", "You cannot access this reservation", 403)


async def list_reservations(db: AsyncSession, user: User) -> list[Reservation]:
    """Guest + host reservations for the current user (ADMIN sees all)."""
    if user.role == Role.ADMIN.value:
        return await reservation_repo.list_all(db)
    return await reservation_repo.list_for_user(db, user.id)


async def get_reservation(
    db: AsyncSession, reservation_id: int, user: User
) -> Reservation:
    reservation = await _get_or_404(db, reservation_id)
    _assert_visible(reservation, user)
    return reservation


async def list_busy_ranges(
    db: AsyncSession, apartment_id: int
) -> list[Reservation]:
    """Public: active (PENDING/APPROVED) date spans for an apartment."""
    apartment = await apartment_repo.get_by_id(db, apartment_id)
    if apartment is None:
        raise AppError("not_found", "Apartment not found", 404)
    return await reservation_repo.list_active_by_apartment(db, apartment_id)


async def list_for_apartment(
    db: AsyncSession, apartment_id: int, user: User
) -> list[Reservation]:
    """Reservations for one apartment - only its owner or an ADMIN may view."""
    apartment = await apartment_repo.get_by_id(db, apartment_id)
    if apartment is None:
        raise AppError("not_found", "Apartment not found", 404)
    if user.role != Role.ADMIN.value and apartment.owner_id != user.id:
        raise AppError(
            "forbidden", "Only the apartment owner can view these reservations", 403
        )
    return await reservation_repo.list_by_apartment(db, apartment_id)


# ---- create ---------------------------------------------------

async def _validate_booking(
    db: AsyncSession,
    apartment,
    check_in: date,
    check_out: date,
    guests_count: int,
    *,
    exclude_id: int | None = None,
) -> None:
    # Rule 1 - defensive (schema already blocks this with 422)
    if check_out <= check_in:
        raise AppError("invalid_dates", "check_out must be later than check_in", 422)

    # Rule 2 - guest count vs capacity
    if guests_count > apartment.max_guests:
        raise AppError(
            "too_many_guests",
            f"This apartment accommodates at most {apartment.max_guests} guests",
            422,
        )

    # Rule 3 - overlapping active reservations
    clashes = await reservation_repo.find_overlapping(
        db, apartment.id, check_in, check_out, exclude_id=exclude_id
    )
    if clashes:
        raise AppError(
            "dates_unavailable",
            "The apartment is already booked for the selected dates",
            409,
        )


async def create_reservation(
    db: AsyncSession, apartment_id: int, body: ReservationCreate, user: User
) -> Reservation:
    apartment = await apartment_repo.get_by_id(db, apartment_id)
    if apartment is None:
        raise AppError("not_found", "Apartment not found", 404)

    if apartment.owner_id == user.id:
        raise AppError("forbidden", "You cannot book your own apartment", 403)

    await _validate_booking(
        db, apartment, body.check_in, body.check_out, body.guests_count
    )

    reservation = Reservation(
        apartment_id=apartment_id,
        guest_id=user.id,
        check_in=body.check_in,
        check_out=body.check_out,
        guests_count=body.guests_count,
        status=S.PENDING.value,
    )
    await reservation_repo.create(db, reservation)
    return await _get_or_404(db, reservation.id)


# ---- update / delete ----------------------------------------

async def update_reservation(
    db: AsyncSession, reservation_id: int, body: ReservationUpdate, user: User
) -> Reservation:
    reservation = await _get_or_404(db, reservation_id)
    relation = _relation(reservation, user)
    if relation not in ("guest", "admin"):
        raise AppError("forbidden", "Only the guest can edit this reservation", 403)
    if reservation.status != S.PENDING.value:
        raise AppError(
            "not_editable", "Only a PENDING reservation can be edited", 409
        )

    check_in = body.check_in or reservation.check_in
    check_out = body.check_out or reservation.check_out
    guests_count = body.guests_count or reservation.guests_count

    await _validate_booking(
        db,
        reservation.apartment,
        check_in,
        check_out,
        guests_count,
        exclude_id=reservation.id,
    )

    reservation.check_in = check_in
    reservation.check_out = check_out
    reservation.guests_count = guests_count
    await db.flush()
    return await _get_or_404(db, reservation.id)


async def delete_reservation(
    db: AsyncSession, reservation_id: int, user: User
) -> None:
    reservation = await _get_or_404(db, reservation_id)
    relation = _relation(reservation, user)
    if relation not in ("guest", "admin"):
        raise AppError("forbidden", "You cannot delete this reservation", 403)
    await reservation_repo.delete(db, reservation)


# ---- workflow (Rule 4) ------------------------------------

async def _transition(
    db: AsyncSession, reservation_id: int, target: ReservationStatus, user: User
) -> Reservation:
    reservation = await _get_or_404(db, reservation_id)
    relation = _relation(reservation, user)
    if relation is None:
        raise AppError("forbidden", "You cannot access this reservation", 403)

    key = (reservation.status, target.value)
    required = _ALLOWED_TRANSITIONS.get(key)
    if required is None:
        raise AppError(
            "invalid_transition",
            f"Cannot change status {reservation.status} -> {target.value}",
            409,
        )
    if relation != "admin" and relation != required:
        who = "apartment owner" if required == "owner" else "guest"
        raise AppError(
            "forbidden", f"Only the {who} may perform this action", 403
        )

    reservation.status = target.value
    await db.flush()
    return await _get_or_404(db, reservation.id)


async def approve(db, reservation_id, user):
    return await _transition(db, reservation_id, S.APPROVED, user)


async def reject(db, reservation_id, user):
    return await _transition(db, reservation_id, S.REJECTED, user)


async def cancel(db, reservation_id, user):
    return await _transition(db, reservation_id, S.CANCELLED, user)


async def complete(db, reservation_id, user):
    return await _transition(db, reservation_id, S.COMPLETED, user)
