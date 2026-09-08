# =============================================================
# admin_service.py - Admin-only business logic
# =============================================================

from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import AppError
from models.enums import Role
from models.user import User
from repositories import apartment_repo, reservation_repo, user_repo


async def list_users(db: AsyncSession) -> list[User]:
    return await user_repo.list_all(db)


async def list_apartments(db: AsyncSession):
    return await apartment_repo.list_all(db)


async def list_reservations(db: AsyncSession):
    return await reservation_repo.list_all(db)


async def set_user_role(
    db: AsyncSession, user_id: int, role: Role, acting_admin: User
) -> User:
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise AppError("not_found", "User not found", 404)
    if user.id == acting_admin.id:
        raise AppError("forbidden", "You cannot change your own role", 403)
    user.role = role.value
    await db.flush()
    return user


async def delete_user(db: AsyncSession, user_id: int, acting_admin: User) -> None:
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise AppError("not_found", "User not found", 404)
    if user.id == acting_admin.id:
        raise AppError("forbidden", "You cannot delete your own account", 403)
    await user_repo.delete(db, user)
