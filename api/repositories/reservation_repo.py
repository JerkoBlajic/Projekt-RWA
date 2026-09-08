# =============================================================
# reservation_repo.py - Database queries for the Reservation model
# =============================================================

from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.apartment import Apartment
from models.enums import ACTIVE_RESERVATION_STATUSES
from models.reservation import Reservation

_EAGER = (
    selectinload(Reservation.apartment),
    selectinload(Reservation.guest),
)


async def get_by_id(db: AsyncSession, reservation_id: int) -> Reservation | None:
    result = await db.execute(
        select(Reservation).options(*_EAGER).where(Reservation.id == reservation_id)
    )
    return result.scalar_one_or_none()


async def list_all(db: AsyncSession) -> list[Reservation]:
    result = await db.execute(
        select(Reservation).options(*_EAGER).order_by(Reservation.created_at.desc())
    )
    return list(result.scalars().all())


async def list_for_user(db: AsyncSession, user_id: int) -> list[Reservation]:
    """Reservations where the user is the guest OR owns the apartment."""
    result = await db.execute(
        select(Reservation)
        .options(*_EAGER)
        .join(Apartment, Reservation.apartment_id == Apartment.id)
        .where(or_(Reservation.guest_id == user_id, Apartment.owner_id == user_id))
        .order_by(Reservation.created_at.desc())
    )
    return list(result.scalars().all())


async def list_by_apartment(db: AsyncSession, apartment_id: int) -> list[Reservation]:
    result = await db.execute(
        select(Reservation)
        .options(*_EAGER)
        .where(Reservation.apartment_id == apartment_id)
        .order_by(Reservation.check_in)
    )
    return list(result.scalars().all())


async def list_active_by_apartment(
    db: AsyncSession, apartment_id: int
) -> list[Reservation]:
    """Only PENDING/APPROVED reservations - the ones that block dates."""
    result = await db.execute(
        select(Reservation)
        .where(Reservation.apartment_id == apartment_id)
        .where(Reservation.status.in_(ACTIVE_RESERVATION_STATUSES))
        .order_by(Reservation.check_in)
    )
    return list(result.scalars().all())


async def find_overlapping(
    db: AsyncSession,
    apartment_id: int,
    check_in: date,
    check_out: date,
    *,
    exclude_id: int | None = None,
) -> list[Reservation]:
    """
    Active reservations for the apartment whose date range overlaps
    [check_in, check_out). Two ranges overlap when:
        existing.check_in < new.check_out AND existing.check_out > new.check_in
    """
    stmt = (
        select(Reservation)
        .where(Reservation.apartment_id == apartment_id)
        .where(Reservation.status.in_(ACTIVE_RESERVATION_STATUSES))
        .where(Reservation.check_in < check_out)
        .where(Reservation.check_out > check_in)
    )
    if exclude_id is not None:
        stmt = stmt.where(Reservation.id != exclude_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, reservation: Reservation) -> Reservation:
    db.add(reservation)
    await db.flush()
    return reservation


async def delete(db: AsyncSession, reservation: Reservation) -> None:
    await db.delete(reservation)
    await db.flush()
