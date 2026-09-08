# =============================================================
# amenity_service.py - Amenity business logic
# =============================================================

from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.amenity import Amenity
from repositories import amenity_repo
from schemas.amenity import AmenityCreate


async def list_amenities(db: AsyncSession) -> list[Amenity]:
    return await amenity_repo.list_all(db)


async def create_amenity(db: AsyncSession, body: AmenityCreate) -> Amenity:
    if await amenity_repo.get_by_name(db, body.name):
        raise AppError("duplicate", "Amenity already exists", 409)
    return await amenity_repo.create(db, Amenity(name=body.name))
