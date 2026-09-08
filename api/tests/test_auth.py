# =============================================================
# test_auth.py - registration, login, tokens, /auth/me
# =============================================================

from httpx import AsyncClient

from tests.conftest import auth_headers


async def test_register_creates_user_and_tokens(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"username": "newbie", "email": "newbie@example.com", "password": "supersecret"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["username"] == "newbie"
    assert body["user"]["role"] == "USER"
    assert body["tokens"]["access_token"]
    assert body["tokens"]["refresh_token"]


async def test_register_duplicate_username(client: AsyncClient, user_a):
    resp = await client.post(
        "/auth/register",
        json={"username": "alice", "email": "other@example.com", "password": "supersecret"},
    )
    assert resp.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"username": "shorty", "email": "s@example.com", "password": "abc"},
    )
    assert resp.status_code == 422


async def test_login_ok(client: AsyncClient, user_a):
    resp = await client.post(
        "/auth/login", json={"username": "alice", "password": "password123"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] and data["refresh_token"]
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, user_a):
    resp = await client.post(
        "/auth/login", json={"username": "alice", "password": "nope"}
    )
    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


async def test_login_unknown_user(client: AsyncClient):
    resp = await client.post(
        "/auth/login", json={"username": "ghost", "password": "whatever"}
    )
    assert resp.status_code == 401


async def test_refresh_returns_new_tokens(client: AsyncClient, user_a):
    login = await client.post(
        "/auth/login", json={"username": "alice", "password": "password123"}
    )
    refresh_token = login.json()["refresh_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


async def test_refresh_rejects_access_token(client: AsyncClient, user_a):
    login = await client.post(
        "/auth/login", json={"username": "alice", "password": "password123"}
    )
    access_token = login.json()["access_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


async def test_me_returns_current_user(client: AsyncClient, user_a):
    headers = await auth_headers(client, "alice")
    resp = await client.get("/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "alice"


async def test_me_without_token_is_401(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_with_garbage_token_is_401(client: AsyncClient):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert resp.status_code == 401
