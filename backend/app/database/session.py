"""Engine and session factory. URL comes from environment variables via SQLAlchemy 2.0."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.database.base import Base

_settings = get_settings()
connect_args = {}
db_url = _settings.DATABASE_URL

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif db_url.startswith("postgresql://"):
    # SQLAlchemy 2.0 recommends postgresql+psycopg:// for psycopg 3 or postgresql+psycopg2://
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(
    db_url,
    connect_args=connect_args,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables for local/dev in PostgreSQL / SQLite."""
    from backend.app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
