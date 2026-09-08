# =============================================================
# test_ownership.py - apartment ownership + admin authorization
# =============================================================

from httpx import AsyncClient

from tests.conftest import auth_headers


async def test_owner_can_edit_own_apartment(client: AsyncClient, apartment_a, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.put(
        f"/apartments/{apartment_a.id}", json={"title": "Renovated Place"}, headers=headers
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renovated Place"


async def test_other_user_cannot_edit_apartment(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    resp = await client.put(
        f"/apartments/{apartment_a.id}", json={"title": "Hijacked"}, headers=headers
    )
    assert resp.status_code == 403


async def test_other_user_cannot_delete_apartment(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    resp = await client.delete(f"/apartments/{apartment_a.id}", headers=headers)
    assert resp.status_code == 403


async def test_owner_can_delete_own_apartment(client: AsyncClient, apartment_a, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.delete(f"/apartments/{apartment_a.id}", headers=headers)
    assert resp.status_code == 204


async def test_admin_can_edit_any_apartment(client: AsyncClient, apartment_a, admin):
    headers = await auth_headers(client, "admin")
    resp = await client.put(
        f"/apartments/{apartment_a.id}", json={"title": "Admin Edit"}, headers=headers
    )
    assert resp.status_code == 200


async def test_unauthenticated_create_apartment_is_401(client: AsyncClient):
    resp = await client.post(
        "/apartments",
        json={
            "title": "No Auth", "description": "x", "address": "y 1", "city": "Split",
            "price_per_night": 50, "max_guests": 2, "bedrooms": 1, "bathrooms": 1,
        },
    )
    assert resp.status_code == 401


async def test_user_cannot_reach_admin_endpoint(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.get("/admin/users", headers=headers)
    assert resp.status_code == 403


async def test_admin_can_reach_admin_endpoint(client: AsyncClient, admin):
    headers = await auth_headers(client, "admin")
    resp = await client.get("/admin/users", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


async def test_missing_apartment_returns_404(client: AsyncClient):
    resp = await client.get("/apartments/999999")
    assert resp.status_code == 404
