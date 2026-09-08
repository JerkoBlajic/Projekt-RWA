# Apartment Rental Management

A full-stack web application for managing apartments and reservations.
Property owners list and manage apartments and handle booking requests;
guests browse apartments and make reservations.

Course project — mandatory stack and architecture per the assignment.

---

## 1. Technologies

| Layer | Stack |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | PostgreSQL 16 |
| Auth | JWT access + refresh tokens, bcrypt password hashing |
| Tests | pytest, pytest-asyncio, httpx (SQLite in-memory) |
| Frontend | Vue 3, Vite, Vue Router, Pinia, Axios |
| Infra | Docker Compose (PostgreSQL), Git / GitHub |

---

## 2. Project structure (monorepo)

```
apartment-rental-management/
├── api/                       # FastAPI backend (layered architecture)
│   ├── main.py                # App factory + router wiring
│   ├── seed.py                # Development seed data
│   ├── core/                  # config, database, security, jwt, deps, errors
│   ├── routers/               # HTTP layer only (no business logic, no SQL)
│   ├── services/              # business logic, authorization, ownership, workflow
│   ├── repositories/          # ALL database queries
│   ├── models/                # SQLAlchemy 2.0 ORM models
│   ├── schemas/               # Pydantic request/response models
│   ├── alembic/               # migrations (source of truth = models)
│   ├── alembic.ini
│   ├── requirements.txt
│   └── tests/                 # pytest: auth, authorization, ownership, rules
├── web/                       # Vue 3 SPA
│   ├── src/
│   │   ├── main.js            # bootstrap: Pinia + Router + mount
│   │   ├── router/            # routes + navigation guards
│   │   ├── stores/            # Pinia: auth.js, apartments.js, reservations.js
│   │   ├── api/               # centralized API client (client.js + per-domain)
│   │   ├── components/        # NavBar, ApartmentCard, StatusBadge, AsyncState
│   │   └── views/             # 10 pages (see section 8)
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml         # PostgreSQL (+ Adminer)
├── render.yaml                # deployment blueprint
├── .env.example
└── README.md
```

### Layered flow (strictly enforced)

```
HTTP request → Router → Service → Repository → SQLAlchemy model → PostgreSQL
```

* Routers never contain business logic or SQL.
* Services never touch the DB session directly for queries (only `flush`/orchestration).
* Repositories contain every `select`/`insert`/`update`/`delete`.

---

## 3. Prerequisites

* Python ≥ 3.11
* Node.js ≥ 18
* Docker Desktop
* Git

---

## 4. Quick start (local)

```bash
git clone <repo-url>
cd apartment-rental-management
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
```

### 4.1 Start PostgreSQL

```bash
docker compose up -d
```

Postgres listens on `localhost:5432` (change `DB_PORT` in `.env` if taken).

### 4.2 Backend

```bash
cd api
python -m venv .venv
# Windows PowerShell:  .venv\Scripts\Activate.ps1
# Windows cmd:         .venv\Scripts\activate.bat
# Linux/macOS:         source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head          # create the schema
python seed.py                # optional demo data

uvicorn main:app --reload     # http://localhost:8000
```

* Swagger UI: `http://localhost:8000/docs`
* Health: `http://localhost:8000/health`

> The backend reads config from `api/.env` if present, otherwise from the
> repo-root `.env`. A ready `api/.env.example` is included.

### 4.3 Frontend

```bash
cd web
cp .env.example .env          # sets VITE_API_URL=http://localhost:8000
npm install
npm run dev                   # http://localhost:5173
```

### Demo credentials (after `python seed.py`)

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | ADMIN |
| `ana` | `password123` | USER (owns apartments) |
| `marko` | `password123` | USER (owns apartments) |
| `iva` | `password123` | USER (has a reservation) |

---

## 5. Database

PostgreSQL. Five tables, meaningful relationships:

| Table | Purpose |
|---|---|
| `users` | id, username, email, password_hash, role, created_at |
| `apartments` | id, **owner_id → users**, title, image, description, address, city, price_per_night, max_guests, bedrooms, bathrooms, created_at, updated_at |
| `reservations` | id, **apartment_id → apartments**, **guest_id → users**, check_in, check_out, guests_count, status, created_at |
| `amenities` | id, name |
| `apartment_amenities` | **apartment_id → apartments**, **amenity_id → amenities** (composite PK) |

Relationships:

* `users 1 : N apartments` (a user can own many apartments)
* `users 1 : N reservations` (a user can make many reservations)
* `apartments 1 : N reservations`
* `apartments N : M amenities` (through `apartment_amenities`)

`reservations.status ∈ {PENDING, APPROVED, REJECTED, CANCELLED, COMPLETED}`
`users.role ∈ {USER, ADMIN}`

---

## 6. Alembic migrations

The SQLAlchemy models are the single source of truth. Never create tables by hand.

```bash
cd api
alembic upgrade head                         # apply all migrations
alembic downgrade -1                          # roll back the last one
alembic revision --autogenerate -m "message" # generate a new migration
alembic history                              # list migrations
alembic check                                # models vs. DB drift check
```

Reset everything:

```bash
docker compose down -v
docker compose up -d
cd api && alembic upgrade head && python seed.py
```

---

## 7. Tests

```bash
cd api
pytest            # 51 tests, SQLite in-memory, no Docker needed
```

Coverage:

* **Authentication** — register, login, invalid login, access token, refresh token, `/auth/me`.
* **Authorization** — USER reaches own resources; USER gets `403` on every `/admin/*`; ADMIN reaches `/admin/*`; unauthenticated gets `401`.
* **Ownership** — owner can edit/delete own apartment; another user gets `403`; ADMIN can edit any.
* **Business rules** — `check_out > check_in`; `guests_count ≤ max_guests`; overlapping reservations rejected with `409`; invalid status transitions rejected (`REJECTED → APPROVED` etc.); valid transitions succeed; a cancelled reservation frees its dates.

---

## 8. Frontend pages (SPA, 10 routes)

| Route | Page | Access |
|---|---|---|
| `/login` | Login form | public |
| `/register` | Registration | public |
| `/apartments` | Browse + filter (city / price / guests) | public |
| `/apartments/:id` | Apartment detail + booking form + owner's reservation panel | public |
| `/apartments/create` | Create apartment | auth |
| `/apartments/:id/edit` | Edit apartment | auth (owner) |
| `/dashboard` | Personal overview (KPIs, my apartments, activity) | auth |
| `/my-apartments` | Manage own apartments | auth |
| `/my-reservations` | Trips I booked + requests for my apartments | auth |
| `/admin` | Admin dashboard: users / apartments / reservations | ADMIN |
| `*` | 404 | public |

Navigation is SPA-only (Vue Router, no full reload). Route guards in
`web/src/router/index.js` redirect unauthenticated users to `/login`
(with `?redirect=`) and non-admins away from `/admin`.

### Login flow

1. Login form posts `username` / `password` to `POST /auth/login`.
2. Tokens stored in `localStorage`; current user loaded into the Pinia `auth` store.
3. The Axios client attaches `Authorization: Bearer <access>` to every request.
4. On `401`, the client calls `POST /auth/refresh` once (single-flight) and replays the request.
5. If refresh fails, the session is cleared and the user is sent to `/login?expired=1`.
6. After login the user lands on `/dashboard` (or the `redirect` target).

### UX states

Every data view renders **loading** (spinner), **error** (message + retry),
and **empty** (e.g. "You don't have any apartments yet.") through the shared
`AsyncState.vue` component. Server errors are shown as readable text, e.g.
*"The apartment is already booked for the selected dates."*

---

## 9. API endpoints

### Auth
| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register` | `201`, returns user + tokens |
| POST | `/auth/login` | returns access + refresh token |
| POST | `/auth/refresh` | new token pair from a refresh token |
| GET | `/auth/me` | current user (requires access token) |

### Apartments
| Method | Path | Notes |
|---|---|---|
| GET | `/apartments` | public list, `?city=&max_price=&guests=` |
| POST | `/apartments` | `201`, auth |
| GET | `/apartments/{id}` | public |
| PUT | `/apartments/{id}` | auth + ownership (or ADMIN) |
| DELETE | `/apartments/{id}` | `204`, auth + ownership (or ADMIN) |
| GET | `/apartments/{id}/reservations` | owner/ADMIN — reservations for that apartment |
| POST | `/apartments/{id}/reservations` | `201` — create a reservation (nested) |

### Current user (nested)
| Method | Path |
|---|---|
| GET | `/users/me/apartments` |
| GET | `/users/me/reservations` |

### Reservations
| Method | Path | Notes |
|---|---|---|
| GET | `/reservations` | own guest + host rows (ADMIN: all) |
| GET | `/reservations/{id}` | guest / apartment owner / ADMIN |
| PUT | `/reservations/{id}` | guest, only while `PENDING` |
| DELETE | `/reservations/{id}` | `204`, guest / ADMIN |
| POST | `/reservations/{id}/approve` | owner / ADMIN |
| POST | `/reservations/{id}/reject` | owner / ADMIN |
| POST | `/reservations/{id}/cancel` | guest / ADMIN |
| POST | `/reservations/{id}/complete` | owner / ADMIN |

### Amenities
| Method | Path | Notes |
|---|---|---|
| GET | `/amenities` | public |
| POST | `/amenities` | ADMIN, `201` |

### Admin
| Method | Path | Notes |
|---|---|---|
| GET | `/admin/users` | ADMIN only, else `403` |
| PATCH | `/admin/users/{id}` | change role |
| DELETE | `/admin/users/{id}` | `204` |
| GET | `/admin/apartments` | ADMIN |
| GET | `/admin/reservations` | ADMIN |

### HTTP status codes

`200` OK · `201` Created · `204` No Content · `400` bad request ·
`401` unauthenticated · `403` wrong role / not owner · `404` missing resource ·
`409` overlapping reservation or invalid status transition · `422` validation error.

---

## 10. Business rules (service layer)

1. **Dates** — `check_out` must be after `check_in` (schema → `422`).
2. **Capacity** — `guests_count ≤ apartment.max_guests` (`422 too_many_guests`).
3. **No overlap** — a new reservation cannot overlap an existing `PENDING`/`APPROVED`
   reservation for the same apartment (`409 dates_unavailable`).
4. **Workflow** — allowed transitions only:
   * owner: `PENDING → APPROVED`, `PENDING → REJECTED`, `APPROVED → COMPLETED`
   * guest: `PENDING → CANCELLED`, `APPROVED → CANCELLED`
   * anything else → `409 invalid_transition`.

All four checks live in `api/services/reservation_service.py`, never in routers.

---

## 11. Roles & authorization

* `USER` — browse, manage own apartments, book, manage own reservations,
  approve/reject reservations for apartments they own.
* `ADMIN` — everything above plus `/admin/*` (list all users/apartments/reservations,
  change roles, delete users).

Enforced with FastAPI dependencies: `get_current_user` (401) and
`require_admin` (403). Ownership is checked in the service layer.

---

## 12. Environment variables

| Variable | Used by | Example |
|---|---|---|
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `DB_PORT` | docker-compose | `rental_db` / `rental_user` / `rental_pass` / `5432` |
| `DATABASE_URL` | API | `postgresql+asyncpg://rental_user:rental_pass@localhost:5432/rental_db` |
| `ENV` | API | `dev` / `production` |
| `JWT_SECRET` | API | long random string (**never commit**) |
| `JWT_ISSUER` | API | `apartment-rental-management` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | API | `15` / `7` |
| `CORS_ORIGINS` | API | comma-separated frontend URLs |
| `VITE_API_URL` | web | `http://localhost:8000` (prod: the deployed API URL) |

`.env` is git-ignored; `.env.example` documents every key. Secrets and the
production API URL are **never hardcoded** — the SPA reads `import.meta.env.VITE_API_URL`.

---

## 13. Deployment

The repo ships `render.yaml` (Render.com blueprint) plus `api/Dockerfile` and
`web/Dockerfile` so it also runs on Railway, Fly.io, or any Docker host.

### Render (blueprint)

1. Push the repo to GitHub.
2. Render → **New → Blueprint** → pick the repo. It creates:
   * `rental-db` — managed PostgreSQL,
   * `rental-api` — Docker web service (`api/Dockerfile`); `DATABASE_URL` is wired
     from the database, `JWT_SECRET` is generated. The container runs
     `alembic upgrade head` before starting uvicorn.
   * `rental-web` — static site built from `web/` with SPA rewrite to `index.html`.
3. After the first deploy set the two cross-URLs:
   * `rental-api` → `CORS_ORIGINS = https://rental-web.onrender.com`
   * `rental-web` → `VITE_API_URL = https://rental-api.onrender.com`, then redeploy the site.
4. Seed once (optional): open the `rental-api` shell and run `python seed.py`.

`DATABASE_URL` from managed providers arrives as `postgres://…`; the API rewrites
it to `postgresql+asyncpg://…` automatically (`core/config.py`).

### Railway (alternative)

* New project → Deploy from GitHub → add a PostgreSQL plugin.
* Backend service: root `api/`, Dockerfile build, set `DATABASE_URL` (reference the
  plugin), `JWT_SECRET`, `ENV=production`, `CORS_ORIGINS`.
* Frontend service: root `web/`, build `npm ci && npm run build`, serve `dist/`,
  set `VITE_API_URL` at build time.

---

## 14. Git

Single repository, backend and frontend together (`api/` + `web/`).
`.env`, `.venv/`, `node_modules/`, `dist/` and `__pycache__/` are ignored.
