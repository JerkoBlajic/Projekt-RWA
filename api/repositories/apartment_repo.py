# =============================================================
# apartment_repo.py - Database queries for the Apartment model
# =============================================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.apartment import Apartment

_EAGER = (
    selectinload(Apartment.amenities),
    selectinload(Apartment.owner),
)


async def get_by_id(db: AsyncSession, apartment_id: int) -> Apartment | None:
    result = await db.execute(
        select(Apartment).options(*_EAGER).where(Apartment.id == apartment_id)
    )
    return result.scalar_one_or_none()


async def list_all(
    db: AsyncSession,
    *,
    city: str | None = None,
    max_price: float | None = None,
    guests: int | None = None,
) -> list[Apartment]:
    stmt = select(Apartment).options(*_EAGER).order_by(Apartment.created_at.desc())
    if city:
        stmt = stmt.where(Apartment.city.ilike(f"%{city}%"))
    if max_price is not None:
        stmt = stmt.where(Apartment.price_per_night <= max_price)
    if guests is not None:
        stmt = stmt.where(Apartment.max_guests >= guests)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def list_by_owner(db: AsyncSession, owner_id: int) -> list[Apartment]:
    result = await db.execute(
        select(Apartment)
        .options(*_EAGER)
        .where(Apartment.owner_id == owner_id)
        .order_by(Apartment.created_at.desc())
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, apartment: Apartment) -> Apartment:
    db.add(apartment)
    await db.flush()
    return apartment


async def delete(db: AsyncSession, apartment: Apartment) -> None:
    await db.delete(apartment)
    await db.flush()
