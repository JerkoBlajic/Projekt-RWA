# =============================================================
# config.py - Central application configuration
# =============================================================
# All environment variables are read in ONE place instead of
# scattered os.getenv(...) calls. Benefits:
#   1. Typed configuration (IDE autocompletion)
#   2. Validation at startup
#   3. Sensible defaults for local development
#
# Usage:
#   from core.config import settings
#   print(settings.DATABASE_URL)
# =============================================================

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # "dev" enables debug logging and the Swagger UI.
    ENV: str = "dev"

    # SQLAlchemy async connection string:
    #   postgresql+asyncpg://<user>:<pass>@<host>:<port>/<db>
    DATABASE_URL: str = (
        "postgresql+asyncpg://rental_user:rental_pass@localhost:5432/rental_db"
    )

    # JWT configuration - the secret MUST be overridden in production.
    JWT_SECRET: str = "change-me-in-production"
    JWT_ISSUER: str = "apartment-rental-management"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Comma-separated list of allowed frontend origins for CORS.
    CORS_ORIGINS: str = ""

    @field_validator("DATABASE_URL")
    @classmethod
    def _force_async_driver(cls, v: str) -> str:
        """Managed platforms hand out postgres:// URLs; we need asyncpg."""
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://") :]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip():
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
