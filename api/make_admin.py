# =============================================================
# make_admin.py - promote an existing user to ADMIN
# =============================================================
# Usage (from the api/ directory, or Render's Shell tab):
#   python make_admin.py <username>
#
# There is no self-service way to become an admin (registration
# always creates a USER). Run this once against a user you have
# already registered through the app.
# =============================================================

import asyncio
import sys

from sqlalchemy import select

from core.database import AsyncSessionLocal, engine
from models.enums import Role
from models.user import User


async def promote(username: str) -> None:
    async with AsyncSessionLocal() as db:
        user = (
            await db.execute(select(User).where(User.username == username))
        ).scalar_one_or_none()
        if user is None:
            print(f"No user named '{username}'. Register it in the app first.")
            raise SystemExit(1)
        if user.role == Role.ADMIN.value:
            print(f"'{username}' is already an ADMIN.")
        else:
            user.role = Role.ADMIN.value
            await db.commit()
            print(f"'{username}' is now an ADMIN.")
    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <username>")
        raise SystemExit(1)
    asyncio.run(promote(sys.argv[1]))
