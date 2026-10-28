from sqlalchemy.orm import Session

from backend.app.models.category import Category
from backend.app.models.enums import DEFAULT_CATEGORIES


def seed_categories(db: Session) -> None:
    existing = {row.slug for row in db.query(Category).all()}
    for name, slug, is_income in DEFAULT_CATEGORIES:
        if slug not in existing:
            db.add(Category(name=name, slug=slug, is_income=is_income))
    db.commit()
