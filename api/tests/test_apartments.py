# =============================================================
# test_apartments.py - apartment CRUD + validation + amenities
# =============================================================

from httpx import AsyncClient

from tests.conftest import auth_headers

VALID = {
    "title": "Test Flat",
    "description": "Lovely",
    "address": "Somewhere 5",
    "city": "Rijeka",
    "price_per_night": 90,
    "max_guests": 3,
    "bedrooms": 1,
    "bathrooms": 1,
}


async def test_public_list_apartments(client: AsyncClient, apartment_a):
    resp = await client.get("/apartments")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


async def test_create_apartment_201_with_amenities(client: AsyncClient, user_a, amenities):
    headers = await auth_headers(client, "alice")
    payload = {**VALID, "amenity_ids": [amenities[0].id, amenities[1].id]}
    resp = await client.post("/apartments", json=payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["owner_id"] == user_a.id
    assert {a["name"] for a in body["amenities"]} == {"WiFi", "Parking"}


async def test_create_apartment_rejects_zero_price(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.post("/apartments", json={**VALID, "price_per_night": 0}, headers=headers)
    assert resp.status_code == 422


async def test_create_apartment_rejects_zero_max_guests(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.post("/apartments", json={**VALID, "max_guests": 0}, headers=headers)
    assert resp.status_code == 422


async def test_create_apartment_rejects_negative_bedrooms(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.post("/apartments", json={**VALID, "bedrooms": -1}, headers=headers)
    assert resp.status_code == 422


async def test_list_my_apartments(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    assert (await client.get("/users/me/apartments", headers=headers_b)).json() == []

    headers_a = await auth_headers(client, "alice")
    mine = await client.get("/users/me/apartments", headers=headers_a)
    assert mine.status_code == 200
    assert len(mine.json()) == 1


async def test_create_apartment_with_area(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.post("/apartments", json={**VALID, "area_sqm": 65}, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["area_sqm"] == 65


async def test_area_sqm_is_optional(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.post("/apartments", json=VALID, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["area_sqm"] is None


async def test_area_sqm_must_be_positive(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.post("/apartments", json={**VALID, "area_sqm": 0}, headers=headers)
    assert resp.status_code == 422


async def test_amenities_endpoint(client: AsyncClient, amenities):
    resp = await client.get("/amenities")
    assert resp.status_code == 200
    assert len(resp.json()) == 3
