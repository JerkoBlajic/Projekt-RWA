# =============================================================
# seed.py - Development seed data
# =============================================================
# Run from the api/ directory, after `alembic upgrade head`:
#   python seed.py
#
# Idempotent: skips rows that already exist, safe to re-run.
# =============================================================

import asyncio
import logging
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from core.database import AsyncSessionLocal, engine
from core.security import hash_password
from models.amenity import Amenity
from models.apartment import Apartment
from models.enums import ReservationStatus, Role
from models.reservation import Reservation
from models.user import User

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("seed")

AMENITIES = ["WiFi", "Parking", "Air conditioning", "Pool", "TV", "Kitchen"]

USERS = [
    {"username": "admin", "email": "admin@example.com", "password": "admin123", "role": Role.ADMIN.value},
    {"username": "ana", "email": "ana@example.com", "password": "password123", "role": Role.USER.value},
    {"username": "marko", "email": "marko@example.com", "password": "password123", "role": Role.USER.value},
    {"username": "iva", "email": "iva@example.com", "password": "password123", "role": Role.USER.value},
]

APARTMENTS = [
    {
        "owner": "ana",
        "title": "Sea View Studio",
        "image": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800",
        "description": "Cosy studio 5 minutes from the beach.",
        "address": "Obala 12", "city": "Split",
        "price_per_night": Decimal("75.00"), "max_guests": 2, "bedrooms": 1, "bathrooms": 1,
        "amenities": ["WiFi", "Air conditioning", "Kitchen"],
    },
    {
        "owner": "ana",
        "title": "Old Town Loft",
        "image": "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800",
        "description": "Bright loft in the heart of the old town.",
        "address": "Kralja Tomislava 3", "city": "Zadar",
        "price_per_night": Decimal("110.00"), "max_guests": 4, "bedrooms": 2, "bathrooms": 1,
        "amenities": ["WiFi", "TV", "Kitchen", "Parking"],
    },
    {
        "owner": "marko",
        "title": "Family House with Pool",
        "image": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800",
        "description": "Spacious house with a private pool and garden.",
        "address": "Vinogradska 44", "city": "Zagreb",
        "price_per_night": Decimal("180.00"), "max_guests": 6, "bedrooms": 3, "bathrooms": 2,
        "amenities": ["WiFi", "Pool", "Parking", "Air conditioning", "TV", "Kitchen"],
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # amenities
        amenities: dict[str, Amenity] = {}
        for name in AMENITIES:
            row = (await db.execute(select(Amenity).where(Amenity.name == name))).scalar_one_or_none()
            if row is None:
                row = Amenity(name=name)
                db.add(row)
                await db.flush()
                log.info("amenity: %s", name)
            amenities[name] = row

        # users
        users: dict[str, User] = {}
        for u in USERS:
            row = (await db.execute(select(User).where(User.username == u["username"]))).scalar_one_or_none()
            if row is None:
                row = User(
                    username=u["username"], email=u["email"],
                    password_hash=hash_password(u["password"]), role=u["role"],
                )
                db.add(row)
                await db.flush()
                log.info("user: %s (%s)", u["username"], u["role"])
            users[u["username"]] = row

        # apartments
        made: list[Apartment] = []
        for a in APARTMENTS:
            row = (await db.execute(select(Apartment).where(Apartment.title == a["title"]))).scalar_one_or_none()
            if row is None:
                row = Apartment(
                    owner_id=users[a["owner"]].id,
                    title=a["title"], image=a["image"], description=a["description"],
                    address=a["address"], city=a["city"],
                    price_per_night=a["price_per_night"], max_guests=a["max_guests"],
                    bedrooms=a["bedrooms"], bathrooms=a["bathrooms"],
                    amenities=[amenities[n] for n in a["amenities"]],
                )
                db.add(row)
                await db.flush()
                log.info("apartment: %s", a["title"])
            made.append(row)

        # one sample reservation: iva books marko's house
        existing = (
            await db.execute(
                select(Reservation).where(Reservation.guest_id == users["iva"].id)
            )
        ).scalar_one_or_none()
        if existing is None and made:
            house = made[-1]
            db.add(
                Reservation(
                    apartment_id=house.id,
                    guest_id=users["iva"].id,
                    check_in=date.today() + timedelta(days=14),
                    check_out=date.today() + timedelta(days=18),
                    guests_count=3,
                    status=ReservationStatus.PENDING.value,
                )
            )
            log.info("reservation: iva -> %s", house.title)

        await db.commit()
    await engine.dispose()
    log.info("seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
