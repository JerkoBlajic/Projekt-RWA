# =============================================================
# main.py - App factory + router wiring
# =============================================================
# Run locally:
#   uvicorn main:app --reload      (from the api/ directory)
# =============================================================

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from core.bootstrap import ensure_bootstrap_admin, ensure_default_amenities
from core.config import settings
from core.errors import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from routers.admin import router as admin_router
from routers.amenities import router as amenities_router
from routers.apartments import router as apartments_router
from routers.auth import router as auth_router
from routers.health import router as health_router
from routers.reservations import router as reservations_router
from routers.users import router as users_router

logging.basicConfig(
    level=logging.DEBUG if settings.ENV == "dev" else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Runs once on startup (after `alembic upgrade head` in the Docker CMD).
    await ensure_default_amenities()
    await ensure_bootstrap_admin()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Apartment Rental Management API",
        version="1.0.0",
        description="Manage apartments, owners, guests and reservations.",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(apartments_router, prefix="/apartments", tags=["apartments"])
    app.include_router(reservations_router, prefix="/reservations", tags=["reservations"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(amenities_router, prefix="/amenities", tags=["amenities"])
    app.include_router(admin_router, prefix="/admin", tags=["admin"])

    logger.info("Application ready (env=%s)", settings.ENV)
    return app


app = create_app()
