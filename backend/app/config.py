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

    # PostgreSQL / SQLite connection string
    DATABASE_URL: str = "postgresql+psycopg://postgres:Ninad%231973@localhost:5432/finpulse"

    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # LLM / AI Advisory configuration
    LLM_PROVIDER: str = "gemini"
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Plaid Sandbox integration
    PLAID_CLIENT_ID: str = ""
    PLAID_SECRET: str = ""
    PLAID_ENV: str = "sandbox"

    LOG_LEVEL: str = "INFO"

    # Setu Account Aggregator (AA) Sandbox
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
