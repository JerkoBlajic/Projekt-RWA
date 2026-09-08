# =============================================================
# apartment_service.py - Apartment business logic + ownership
# =============================================================
# Ownership rule: a user may edit/delete only their own apartments.
# ADMIN may act on any apartment. Violations raise 403.
# =============================================================

from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.apartment import Apartment
from models.enums import Role
from models.user import User
from repositories import amenity_repo, apartment_repo
from schemas.apartment import ApartmentCreate, ApartmentUpdate


async def _get_or_404(db: AsyncSession, apartment_id: int) -> Apartment:
    apartment = await apartment_repo.get_by_id(db, apartment_id)
    if apartment is None:
        raise AppError("not_found", "Apartment not found", 404)
    return apartment


def _assert_can_manage(apartment: Apartment, user: User) -> None:
    if user.role != Role.ADMIN.value and apartment.owner_id != user.id:
        raise AppError("forbidden", "You can only manage your own apartments", 403)


async def list_apartments(
    db: AsyncSession, *, city=None, max_price=None, guests=None
) -> list[Apartment]:
    return await apartment_repo.list_all(
        db, city=city, max_price=max_price, guests=guests
    )


async def list_my_apartments(db: AsyncSession, user: User) -> list[Apartment]:
    return await apartment_repo.list_by_owner(db, user.id)


async def get_apartment(db: AsyncSession, apartment_id: int) -> Apartment:
    return await _get_or_404(db, apartment_id)


async def create_apartment(
    db: AsyncSession, body: ApartmentCreate, user: User
) -> Apartment:
    apartment = Apartment(
        owner_id=user.id,
        title=body.title,
        image=body.image,
        description=body.description or "",
        address=body.address,
        city=body.city,
        price_per_night=body.price_per_night,
        max_guests=body.max_guests,
        bedrooms=body.bedrooms,
        bathrooms=body.bathrooms,
        area_sqm=body.area_sqm,
    )
    if body.amenity_ids:
        apartment.amenities = await amenity_repo.list_by_ids(db, body.amenity_ids)
    await apartment_repo.create(db, apartment)
    return await _get_or_404(db, apartment.id)


async def update_apartment(
    db: AsyncSession, apartment_id: int, body: ApartmentUpdate, user: User
) -> Apartment:
    apartment = await _get_or_404(db, apartment_id)
    _assert_can_manage(apartment, user)

    data = body.model_dump(exclude_unset=True)
    amenity_ids = data.pop("amenity_ids", None)
    for field, value in data.items():
        setattr(apartment, field, value)
    if amenity_ids is not None:
        apartment.amenities = await amenity_repo.list_by_ids(db, amenity_ids)

    await db.flush()
    return await _get_or_404(db, apartment.id)


async def delete_apartment(db: AsyncSession, apartment_id: int, user: User) -> None:
    apartment = await _get_or_404(db, apartment_id)
    _assert_can_manage(apartment, user)
    await apartment_repo.delete(db, apartment)
