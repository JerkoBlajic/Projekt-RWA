# =============================================================
# amenity_repo.py - Database queries for the Amenity model
# =============================================================

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.amenity import Amenity


async def list_all(db: AsyncSession) -> list[Amenity]:
    result = await db.execute(select(Amenity).order_by(Amenity.name))
    return list(result.scalars().all())


async def list_by_ids(db: AsyncSession, ids: list[int]) -> list[Amenity]:
    if not ids:
        return []
    result = await db.execute(select(Amenity).where(Amenity.id.in_(ids)))
    return list(result.scalars().all())


async def get_by_name(db: AsyncSession, name: str) -> Amenity | None:
    result = await db.execute(select(Amenity).where(Amenity.name == name))
    return result.scalar_one_or_none()


async def create(db: AsyncSession, amenity: Amenity) -> Amenity:
    db.add(amenity)
    await db.flush()
    return amenity
