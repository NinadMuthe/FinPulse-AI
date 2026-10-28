from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    current_balance: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="user")  # noqa: F821
    forecasts: Mapped[list["Forecast"]] = relationship(back_populates="user")  # noqa: F821
    anomalies: Mapped[list["Anomaly"]] = relationship(back_populates="user")  # noqa: F821
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")  # noqa: F821
    advisory_messages: Mapped[list["AdvisoryMessage"]] = relationship(back_populates="user")  # noqa: F821
