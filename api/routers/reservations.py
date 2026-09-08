# =============================================================
# reservations.py - Reservation endpoints
# =============================================================
#   GET    /reservations              (auth - own guest + host rows)
#   GET    /reservations/{id}         (auth + visibility)
#   PUT    /reservations/{id}         (auth - guest, PENDING only)
#   DELETE /reservations/{id}         (auth - guest/admin)         204
#   POST   /reservations/{id}/approve (auth - owner/admin)
#   POST   /reservations/{id}/reject  (auth - owner/admin)
#   POST   /reservations/{id}/cancel  (auth - guest/admin)
#   POST   /reservations/{id}/complete(auth - owner/admin)
# =============================================================

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.user import User
from schemas.reservation import ReservationResponse, ReservationUpdate
from services import reservation_service

router = APIRouter()


@router.get("", response_model=list[ReservationResponse])
async def list_reservations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.list_reservations(db, current_user)


@router.get("/{reservation_id}", response_model=ReservationResponse)
async def get_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.get_reservation(db, reservation_id, current_user)


@router.put("/{reservation_id}", response_model=ReservationResponse)
async def update_reservation(
    reservation_id: int,
    body: ReservationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.update_reservation(
        db, reservation_id, body, current_user
    )


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await reservation_service.delete_reservation(db, reservation_id, current_user)


@router.post("/{reservation_id}/approve", response_model=ReservationResponse)
async def approve_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.approve(db, reservation_id, current_user)


@router.post("/{reservation_id}/reject", response_model=ReservationResponse)
async def reject_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.reject(db, reservation_id, current_user)


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
async def cancel_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.cancel(db, reservation_id, current_user)


@router.post("/{reservation_id}/complete", response_model=ReservationResponse)
async def complete_reservation(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await reservation_service.complete(db, reservation_id, current_user)
