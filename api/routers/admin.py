# =============================================================
# admin.py - Admin-only endpoints (require_admin -> 403 for USER)
# =============================================================
#   GET    /admin/users
#   PATCH  /admin/users/{id}          (change role)
#   DELETE /admin/users/{id}                              204
#   GET    /admin/apartments
#   GET    /admin/reservations
# =============================================================

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db, require_admin
from models.user import User
from schemas.apartment import ApartmentResponse
from schemas.reservation import ReservationResponse
from schemas.user import UserResponse, UserRoleUpdate
from services import admin_service

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    return await admin_service.list_users(db)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    body: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return await admin_service.set_user_role(db, user_id, body.role, admin)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    await admin_service.delete_user(db, user_id, admin)


@router.get("/apartments", response_model=list[ApartmentResponse])
async def list_apartments(db: AsyncSession = Depends(get_db)):
    return await admin_service.list_apartments(db)


@router.get("/reservations", response_model=list[ReservationResponse])
async def list_reservations(db: AsyncSession = Depends(get_db)):
    return await admin_service.list_reservations(db)
