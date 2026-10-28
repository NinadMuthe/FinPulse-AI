"""Seed demo user with historical transactions for rich interactive dashboard testing."""

import csv
import datetime
from pathlib import Path
import sys

# Ensure repository root is on sys.path when executed directly
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.database.session import SessionLocal, init_db
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.utils.security import hash_password
from backend.app.services.categories import seed_categories


def seed_demo_data():
    # Ensure database schema is initialized
    init_db()

    db = SessionLocal()
    seed_categories(db)

    demo_user = db.query(User).filter(User.email == "demo@finpulse.ai").first()
    if not demo_user:
        demo_user = User(
            email="demo@finpulse.ai",
            hashed_password=hash_password("demo"),
            full_name="FinPulse Demo User",
            current_balance=20000.0,
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
    else:
        demo_user.hashed_password = hash_password("demo")
        demo_user.current_balance = 20000.0
        db.commit()

    # Check if user already has transactions
    count = db.query(Transaction).filter(Transaction.user_id == demo_user.id).count()
    if count > 20:
        print(f"Demo user already has {count} transactions.")
        db.close()
        return

    csv_path = REPO_ROOT / "datasets" / "raw" / "transactions.csv"
    if not csv_path.exists():
        print(f"{csv_path} not found. Run 'python ml/preprocessing/generate_dataset.py' first.")
        db.close()
        return

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        added = 0
        for row in reader:
            try:
                tx_date = datetime.date.fromisoformat(row["date"])
            except Exception:
                continue
            t = Transaction(
                user_id=demo_user.id,
                amount=float(row["amount"]),
                merchant=row["merchant"],
                category=row["category"],
                transaction_date=datetime.datetime.combine(tx_date, datetime.time(12, 0)),
                transaction_type=row.get("transaction_type", "debit"),
                source=row.get("source", "sms"),
                description=row.get("description", ""),
                confidence_score=0.95,
            )
            db.add(t)
            added += 1

        db.commit()
        print(f"Seeded {added} transactions into database for user {demo_user.email}!")
    db.close()


if __name__ == "__main__":
    seed_demo_data()
