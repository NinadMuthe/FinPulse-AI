from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction
from backend.app.schemas.transaction import TransactionCreate, TransactionUpdate
from ml.categories.taxonomy import classify_category


from backend.app.models.user import User


def create_transaction(db: Session, user_id: int, payload: TransactionCreate) -> Transaction:
    category = payload.category
    if category == "Other":
        category = classify_category(payload.merchant, payload.description or "")
    row = Transaction(
        user_id=user_id,
        amount=payload.amount,
        merchant=payload.merchant,
        category=category,
        transaction_date=payload.transaction_date or datetime.now(timezone.utc),
        transaction_type=payload.transaction_type,
        source=payload.source,
        description=payload.description,
        confidence_score=payload.confidence_score,
    )
    db.add(row)

    # Immediately adjust user's available balance
    user = db.get(User, user_id)
    if user:
        if payload.transaction_type == "credit":
            user.current_balance = round(user.current_balance + payload.amount, 2)
        else:
            user.current_balance = round(user.current_balance - payload.amount, 2)

    db.commit()
    db.refresh(row)
    return row


def list_transactions(db: Session, user_id: int) -> list[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
        .all()
    )


def get_transaction(db: Session, user_id: int, tx_id: int) -> Transaction | None:
    row = db.get(Transaction, tx_id)
    if row is None or row.user_id != user_id:
        return None
    return row


def update_transaction(db: Session, row: Transaction, payload: TransactionUpdate) -> Transaction:
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def delete_transaction(db: Session, row: Transaction) -> None:
    db.delete(row)
    db.commit()


def to_dicts(rows: list[Transaction]) -> list[dict]:
    return [
        {
            "id": r.id,
            "amount": r.amount,
            "merchant": r.merchant,
            "category": r.category,
            "transaction_date": r.transaction_date,
            "transaction_type": r.transaction_type,
            "source": r.source,
            "description": r.description,
        }
        for r in rows
    ]
