# =============================================================
# test_bootstrap.py - startup helpers (amenity seed, admin bootstrap)
# =============================================================

import core.bootstrap as bootstrap
from core.bootstrap import DEFAULT_AMENITIES, ensure_default_amenities
from models.enums import Role
from repositories import amenity_repo, user_repo
from tests.conftest import TestSessionLocal


async def test_default_amenities_are_seeded_once(monkeypatch, db):
    monkeypatch.setattr(bootstrap, "AsyncSessionLocal", TestSessionLocal)

    await ensure_default_amenities()
    await ensure_default_amenities()  # idempotent - no duplicates

    names = sorted(a.name for a in await amenity_repo.list_all(db))
    assert names == sorted(DEFAULT_AMENITIES)


async def test_bootstrap_admin_promotes_existing_user(monkeypatch, user_a):
    monkeypatch.setattr(bootstrap, "AsyncSessionLocal", TestSessionLocal)
    monkeypatch.setattr(bootstrap.settings, "BOOTSTRAP_ADMIN_USERNAME", "alice")

    await bootstrap.ensure_bootstrap_admin()

    # read back through a fresh session (the change was committed elsewhere)
    async with TestSessionLocal() as fresh:
        refreshed = await user_repo.get_by_username(fresh, "alice")
    assert refreshed.role == Role.ADMIN.value
