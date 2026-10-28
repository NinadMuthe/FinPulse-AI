"""Engine and session factory. URL comes from environment variables."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.database.base import Base

_settings = get_settings()
connect_args = {}
if _settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    _settings.DATABASE_URL,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables for local/dev. Prefer Alembic in production."""
    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
