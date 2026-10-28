from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    is_income: Mapped[bool] = mapped_column(Boolean, default=False)

    merchants: Mapped[list["Merchant"]] = relationship(back_populates="default_category")  # noqa: F821


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    default_category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)

    default_category: Mapped[Category | None] = relationship(back_populates="merchants")
