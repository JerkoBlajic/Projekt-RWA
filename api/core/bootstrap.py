# =============================================================
# bootstrap.py - one-time startup tasks
# =============================================================
# ensure_bootstrap_admin() runs once when the app starts (wired
# into the FastAPI lifespan in main.py). It exists because there
# is no self-service way to become an ADMIN and hosting shells
# can be a paid feature.
#
# Controlled by env vars (see core/config.py):
#   BOOTSTRAP_ADMIN_USERNAME  - required to do anything
#   BOOTSTRAP_ADMIN_PASSWORD  - if the user doesn't exist, create it with this
#   BOOTSTRAP_ADMIN_EMAIL     - optional email for the created user
#
# Behaviour:
#   user exists, not admin  -> promote to ADMIN
#   user exists, is admin   -> nothing
#   user missing + password -> create as ADMIN
#   user missing, no password -> log a warning, do nothing
#
# Idempotent and safe to leave configured; remove the env vars
# once the admin exists.
# =============================================================

import logging

from core.config import settings
from core.database import AsyncSessionLocal
from core.security import hash_password
from models.enums import Role
from models.user import User
from repositories import user_repo

logger = logging.getLogger(__name__)


async def ensure_bootstrap_admin() -> None:
    username = settings.BOOTSTRAP_ADMIN_USERNAME.strip()
    if not username:
        return

    try:
        async with AsyncSessionLocal() as db:
            user = await user_repo.get_by_username(db, username)

            if user is None:
                password = settings.BOOTSTRAP_ADMIN_PASSWORD
                if not password:
                    logger.warning(
                        "Bootstrap admin '%s' not found and no "
                        "BOOTSTRAP_ADMIN_PASSWORD set - skipping.",
                        username,
                    )
                    return
                email = (
                    settings.BOOTSTRAP_ADMIN_EMAIL.strip()
                    or f"{username}@example.com"
                ).lower()
                db.add(
                    User(
                        username=username,
                        email=email,
                        password_hash=hash_password(password),
                        role=Role.ADMIN.value,
                    )
                )
                await db.commit()
                logger.info("Bootstrap admin '%s' created.", username)
            elif user.role != Role.ADMIN.value:
                user.role = Role.ADMIN.value
                await db.commit()
                logger.info("Bootstrap admin '%s' promoted to ADMIN.", username)
            else:
                logger.info("Bootstrap admin '%s' already ADMIN.", username)
    except Exception:  # never block startup on this
        logger.exception("Bootstrap admin step failed; continuing startup.")
