# =============================================================
# apartments.py - Apartment endpoints
# =============================================================
#   GET    /apartments                     (public, filterable)
#   POST   /apartments                     (auth)            201
#   GET    /apartments/{id}                (public)
#   PUT    /apartments/{id}                (auth + ownership)
#   DELETE /apartments/{id}                (auth + ownership) 204
#   POST   /apartments/{id}/reservations   (auth)            201
#   GET    /apartments/{id}/reservations   (auth + ownership)
# =============================================================

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.user import User
from schemas.apartment import ApartmentCreate, ApartmentResponse, ApartmentUpdate
from schemas.reservation import BusyRange, ReservationCreate, ReservationResponse
from services import apartment_service, reservation_service

router = APIRouter()


@router.get("", response_model=list[ApartmentResponse])
async def list_apartments(
    db: AsyncSession = Depends(get_db),
    city: str | None = Query(default=None),
    max_price: float | None = Query(default=None, gt=0),
    guests: int | None = Query(default=None, gt=0),
):
    return await apartment_service.list_apartments(
        db, city=city, max_price=max_price, guests=guests
    )


@router.post("", response_model=ApartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_apartment(
    body: ApartmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await apartment_service.create_apartment(db, body, current_user)


@router.get("/{apartment_id}", response_model=ApartmentResponse)
async def get_apartment(apartment_id: int, db: AsyncSession = Depends(get_db)):
    return await apartment_service.get_apartment(db, apartment_id)


@router.get("/{apartment_id}/availability", response_model=list[BusyRange])
async def apartment_availability(apartment_id: int, db: AsyncSession = Depends(get_db)):
    """Public: date spans that are already booked (no guest details)."""
    return await reservation_service.list_busy_ranges(db, apartment_id)


@router.put("/{apartment_id}", response_model=ApartmentResponse)
async def update_apartment(
    apartment_id: int,
    body: ApartmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await apartment_service.update_apartment(db, apartment_id, body, current_user)


@router.delete("/{apartment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_apartment(
    apartment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await apartment_service.delete_apartment(db, apartment_id, current_user)


# ---- nested reservations -----------------------------------

@router.post(
    "/{apartment_id}/reservations",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reservation(
    apartment_id: int,
    body: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.create_reservation(
        db, apartment_id, body, current_user
    )


@router.get(
    "/{apartment_id}/reservations",
    response_model=list[ReservationResponse],
)
async def list_apartment_reservations(
    apartment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # ownership enforced in the service (only owner/admin may view)
    return await reservation_service.list_for_apartment(db, apartment_id, current_user)
