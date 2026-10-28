"""
config.py — Application configuration.

Reads settings from environment variables. Never hard-code secrets.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application settings pulled from environment variables."""

    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change-me-in-production"

    # SQLite by default so the API runs without PostgreSQL installed.
    # For PostgreSQL: postgresql+psycopg://USER:PASSWORD@localhost:5432/finpulse
    DATABASE_URL: str = "sqlite:///./backend/finpulse.db"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Exactly one LLM provider is used. Leave empty to use the deterministic advisor.
    LLM_PROVIDER: str = "gemini"
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    LOG_LEVEL: str = "INFO"

    # ──────────────────────────────────────────────────────────────────
    # Setu Account Aggregator (AA) Sandbox
    # Leave empty; the /aa/* routes will return HTTP 503 until credentials are set.
    SETU_CLIENT_ID: str = ""
    SETU_CLIENT_SECRET: str = ""
    SETU_PRODUCT_INSTANCE_ID: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
