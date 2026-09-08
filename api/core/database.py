# =============================================================
# database.py - SQLAlchemy async engine, session factory, Base
# =============================================================
# Infrastructure module: defines HOW we connect to the database
# and HOW sessions are created. ORM models live in models/ and
# inherit from the Base class defined here.
# =============================================================

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# Engine - async connection pool towards PostgreSQL (asyncpg driver).
# pool_pre_ping checks a connection is alive before handing it out.
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Session factory. expire_on_commit=False keeps ORM objects usable
# after commit (handy when returning them in API responses).
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base class for every ORM model."""

    pass
