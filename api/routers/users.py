# =============================================================
# users.py - Current-user nested resources
# =============================================================
#   GET /users/me/apartments
#   GET /users/me/reservations
# =============================================================

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.user import User
from schemas.apartment import ApartmentResponse
from schemas.reservation import ReservationResponse
from services import apartment_service, reservation_service

router = APIRouter()


@router.get("/me/apartments", response_model=list[ApartmentResponse])
async def my_apartments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await apartment_service.list_my_apartments(db, current_user)


@router.get("/me/reservations", response_model=list[ReservationResponse])
async def my_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.list_reservations(db, current_user)
