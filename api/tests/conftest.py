# =============================================================
# conftest.py - Test infrastructure (SQLite in-memory)
# =============================================================
# Every test gets a fresh schema (full isolation). StaticPool keeps
# all async sessions on the same in-memory database.
# =============================================================

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import AsyncGenerator

import pytest

# Keep test output readable - silence the very chatty debug loggers.
for _name in ("aiosqlite", "sqlalchemy.engine", "asyncio", "httpx", ""):
    logging.getLogger(_name).setLevel(logging.WARNING)
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.deps import get_db
from core.security import hash_password
from main import app as fastapi_app
from models import Base
from models.amenity import Amenity
from models.apartment import Apartment
from models.enums import Role
from models.user import User

engine_test = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(engine_test.sync_engine, "connect")
def _sqlite_fk_pragma(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = async_sessionmaker(
    bind=engine_test, class_=AsyncSession, expire_on_commit=False
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


fastapi_app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
async def _schema():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---- user fixtures ------------------------------------------

async def _make_user(db: AsyncSession, username: str, role: str) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash=hash_password("password123"),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin(db: AsyncSession) -> User:
    return await _make_user(db, "admin", Role.ADMIN.value)


@pytest.fixture
async def user_a(db: AsyncSession) -> User:
    return await _make_user(db, "alice", Role.USER.value)


@pytest.fixture
async def user_b(db: AsyncSession) -> User:
    return await _make_user(db, "bob", Role.USER.value)


@pytest.fixture
async def amenities(db: AsyncSession) -> list[Amenity]:
    rows = [Amenity(name=n) for n in ("WiFi", "Parking", "Pool")]
    db.add_all(rows)
    await db.commit()
    for r in rows:
        await db.refresh(r)
    return rows


@pytest.fixture
async def apartment_a(db: AsyncSession, user_a: User) -> Apartment:
    """An apartment owned by user_a (alice), capacity 4."""
    apt = Apartment(
        owner_id=user_a.id,
        title="Alice's Place",
        description="Nice flat",
        address="Main St 1",
        city="Split",
        price_per_night=Decimal("100.00"),
        max_guests=4,
        bedrooms=2,
        bathrooms=1,
    )
    db.add(apt)
    await db.commit()
    await db.refresh(apt)
    return apt


# ---- helpers ----------------------------------------------

async def auth_headers(client: AsyncClient, username: str, password: str = "password123") -> dict:
    resp = await client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()
