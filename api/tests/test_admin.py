# =============================================================
# test_admin.py - admin dashboard endpoints + user management
# =============================================================

from httpx import AsyncClient

from tests.conftest import auth_headers


async def test_admin_lists_all_resources(client: AsyncClient, admin, apartment_a):
    headers = await auth_headers(client, "admin")
    assert (await client.get("/admin/users", headers=headers)).status_code == 200
    assert (await client.get("/admin/apartments", headers=headers)).status_code == 200
    assert (await client.get("/admin/reservations", headers=headers)).status_code == 200


async def test_admin_changes_user_role(client: AsyncClient, admin, user_a):
    headers = await auth_headers(client, "admin")
    resp = await client.patch(
        f"/admin/users/{user_a.id}", json={"role": "ADMIN"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "ADMIN"


async def test_admin_cannot_delete_self(client: AsyncClient, admin):
    headers = await auth_headers(client, "admin")
    resp = await client.delete(f"/admin/users/{admin.id}", headers=headers)
    assert resp.status_code == 403


async def test_admin_deletes_user_204(client: AsyncClient, admin, user_b):
    headers = await auth_headers(client, "admin")
    resp = await client.delete(f"/admin/users/{user_b.id}", headers=headers)
    assert resp.status_code == 204


async def test_user_forbidden_on_all_admin_routes(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    for path in ("/admin/users", "/admin/apartments", "/admin/reservations"):
        assert (await client.get(path, headers=headers)).status_code == 403


async def test_admin_routes_require_auth(client: AsyncClient):
    assert (await client.get("/admin/users")).status_code == 401
