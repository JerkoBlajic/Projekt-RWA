# =============================================================
# user_repo.py - Database queries for the User model
# =============================================================

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(func.lower(User.email) == email.lower())
    )
    return result.scalar_one_or_none()


async def list_all(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


async def create(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.flush()
    return user


async def delete(db: AsyncSession, user: User) -> None:
    await db.delete(user)
    await db.flush()
