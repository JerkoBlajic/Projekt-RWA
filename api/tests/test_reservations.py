# =============================================================
# test_reservations.py - business rules 1-4 + workflow + ownership
# =============================================================

from httpx import AsyncClient

from tests.conftest import auth_headers, future


async def _book(client, apartment_id, headers, check_in=10, check_out=15, guests=2):
    return await client.post(
        f"/apartments/{apartment_id}/reservations",
        json={
            "check_in": future(check_in),
            "check_out": future(check_out),
            "guests_count": guests,
        },
        headers=headers,
    )


# ---- happy path -------------------------------------------

async def test_create_reservation_is_pending_201(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    resp = await _book(client, apartment_a.id, headers)
    assert resp.status_code == 201
    assert resp.json()["status"] == "PENDING"


async def test_owner_cannot_book_own_apartment(client: AsyncClient, apartment_a, user_a):
    headers = await auth_headers(client, "alice")
    resp = await _book(client, apartment_a.id, headers)
    assert resp.status_code == 403


# ---- Rule 1: check_out must be after check_in --------------

async def test_rule1_checkout_not_after_checkin(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    resp = await client.post(
        f"/apartments/{apartment_a.id}/reservations",
        json={"check_in": future(20), "check_out": future(20), "guests_count": 1},
        headers=headers,
    )
    assert resp.status_code == 422


async def test_rule1_checkout_before_checkin(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    resp = await client.post(
        f"/apartments/{apartment_a.id}/reservations",
        json={"check_in": future(20), "check_out": future(10), "guests_count": 1},
        headers=headers,
    )
    assert resp.status_code == 422


# ---- Rule 2: guests_count <= apartment.max_guests ----------

async def test_rule2_too_many_guests(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    resp = await _book(client, apartment_a.id, headers, guests=5)  # capacity is 4
    assert resp.status_code == 422
    assert resp.json()["code"] == "too_many_guests"


async def test_rule2_max_guests_exact_ok(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    resp = await _book(client, apartment_a.id, headers, guests=4)
    assert resp.status_code == 201


# ---- Rule 3: overlapping reservations -> 409 ---------------

async def test_rule3_overlapping_reservation_conflict(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    first = await _book(client, apartment_a.id, headers_b, check_in=10, check_out=15)
    assert first.status_code == 201

    # different guest, overlapping window 13..18
    other = await client.post(
        "/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": "password123"},
    )
    headers_c = {"Authorization": f"Bearer {other.json()['tokens']['access_token']}"}
    resp = await _book(client, apartment_a.id, headers_c, check_in=13, check_out=18)
    assert resp.status_code == 409
    assert resp.json()["code"] == "dates_unavailable"


async def test_rule3_adjacent_dates_allowed(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    a = await _book(client, apartment_a.id, headers, check_in=10, check_out=15)
    assert a.status_code == 201
    b = await _book(client, apartment_a.id, headers, check_in=15, check_out=20)
    assert b.status_code == 201


async def test_rule3_cancelled_frees_the_dates(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    first = await _book(client, apartment_a.id, headers_b, check_in=10, check_out=15)
    rid = first.json()["id"]
    cancel = await client.post(f"/reservations/{rid}/cancel", headers=headers_b)
    assert cancel.status_code == 200

    second = await _book(client, apartment_a.id, headers_b, check_in=11, check_out=14)
    assert second.status_code == 201


# ---- Rule 4: workflow transitions ------------------------

async def test_rule4_owner_approves_pending(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers_b)).json()["id"]

    headers_a = await auth_headers(client, "alice")
    resp = await client.post(f"/reservations/{rid}/approve", headers=headers_a)
    assert resp.status_code == 200
    assert resp.json()["status"] == "APPROVED"


async def test_rule4_guest_cannot_approve(client: AsyncClient, apartment_a, user_b):
    headers_b = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers_b)).json()["id"]
    resp = await client.post(f"/reservations/{rid}/approve", headers=headers_b)
    assert resp.status_code == 403


async def test_rule4_guest_cancels_approved(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers_b)).json()["id"]
    headers_a = await auth_headers(client, "alice")
    await client.post(f"/reservations/{rid}/approve", headers=headers_a)

    resp = await client.post(f"/reservations/{rid}/cancel", headers=headers_b)
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"


async def test_rule4_rejected_cannot_go_to_approved(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers_b)).json()["id"]
    headers_a = await auth_headers(client, "alice")
    await client.post(f"/reservations/{rid}/reject", headers=headers_a)

    resp = await client.post(f"/reservations/{rid}/approve", headers=headers_a)
    assert resp.status_code == 409
    assert resp.json()["code"] == "invalid_transition"


async def test_rule4_cannot_cancel_completed(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers_b)).json()["id"]
    headers_a = await auth_headers(client, "alice")
    await client.post(f"/reservations/{rid}/approve", headers=headers_a)
    await client.post(f"/reservations/{rid}/complete", headers=headers_a)

    resp = await client.post(f"/reservations/{rid}/cancel", headers=headers_b)
    assert resp.status_code == 409


# ---- visibility / listing -------------------------------

async def test_list_reservations_shows_guest_and_host_rows(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    await _book(client, apartment_a.id, headers_b)

    headers_a = await auth_headers(client, "alice")
    as_host = await client.get("/reservations", headers=headers_a)
    assert as_host.status_code == 200 and len(as_host.json()) == 1

    as_guest = await client.get("/reservations", headers=headers_b)
    assert len(as_guest.json()) == 1


async def test_stranger_cannot_view_reservation(client: AsyncClient, apartment_a, user_a, user_b):
    headers_b = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers_b)).json()["id"]

    reg = await client.post(
        "/auth/register",
        json={"username": "dan", "email": "dan@example.com", "password": "password123"},
    )
    headers_d = {"Authorization": f"Bearer {reg.json()['tokens']['access_token']}"}
    resp = await client.get(f"/reservations/{rid}", headers=headers_d)
    assert resp.status_code == 403


async def test_guest_edits_pending_reservation(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers, check_in=10, check_out=15)).json()["id"]
    resp = await client.put(
        f"/reservations/{rid}",
        json={"check_in": future(12), "check_out": future(16), "guests_count": 3},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["guests_count"] == 3


async def test_guest_deletes_own_reservation_204(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers)).json()["id"]
    resp = await client.delete(f"/reservations/{rid}", headers=headers)
    assert resp.status_code == 204


# ---- public availability ---------------------------------

async def test_availability_is_public_and_lists_active_ranges(
    client: AsyncClient, apartment_a, user_b
):
    empty = await client.get(f"/apartments/{apartment_a.id}/availability")
    assert empty.status_code == 200 and empty.json() == []

    headers = await auth_headers(client, "bob")
    await _book(client, apartment_a.id, headers, check_in=10, check_out=15)

    resp = await client.get(f"/apartments/{apartment_a.id}/availability")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["check_in"] == future(10)
    assert body[0]["check_out"] == future(15)
    assert "guest" not in body[0] and "guest_id" not in body[0]


async def test_availability_excludes_cancelled(client: AsyncClient, apartment_a, user_b):
    headers = await auth_headers(client, "bob")
    rid = (await _book(client, apartment_a.id, headers)).json()["id"]
    await client.post(f"/reservations/{rid}/cancel", headers=headers)

    resp = await client.get(f"/apartments/{apartment_a.id}/availability")
    assert resp.status_code == 200 and resp.json() == []
