from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.transaction import (
    ExtractionResult,
    SmsIngestRequest,
    TransactionCreate,
    TransactionOut,
    TransactionUpdate,
)
from backend.app.services import transactions as tx_service
from backend.app.utils.deps import get_current_user
from ml.nlp.extract import extract_transaction

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_tx(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> TransactionOut:
    return tx_service.create_transaction(db, current.id, payload)


@router.get("", response_model=list[TransactionOut])
def list_tx(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[TransactionOut]:
    return tx_service.list_transactions(db, current.id)


@router.get("/{tx_id}", response_model=TransactionOut)
def get_tx(
    tx_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> TransactionOut:
    row = tx_service.get_transaction(db, current.id, tx_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return row


@router.patch("/{tx_id}", response_model=TransactionOut)
def patch_tx(
    tx_id: int,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> TransactionOut:
    row = tx_service.get_transaction(db, current.id, tx_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx_service.update_transaction(db, row, payload)


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tx(
    tx_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> None:
    row = tx_service.get_transaction(db, current.id, tx_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    tx_service.delete_transaction(db, row)


@router.post("/from-sms", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def ingest_sms(
    payload: SmsIngestRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> TransactionOut:
    extracted = extract_transaction(payload.text)
    if extracted["amount"] is None:
        raise HTTPException(status_code=422, detail="Could not extract a transaction amount from the SMS")
    date_value = (
        datetime.fromisoformat(extracted["date"]).replace(tzinfo=timezone.utc)
        if extracted["date"]
        else datetime.now(timezone.utc)
    )
    create = TransactionCreate(
        amount=extracted["amount"],
        merchant=extracted["merchant"],
        category=extracted["category"],
        transaction_date=date_value,
        transaction_type=extracted["transaction_type"],
        source="sms",
        description=extracted["raw_text"],
        confidence_score=extracted["confidence_score"],
    )
    return tx_service.create_transaction(db, current.id, create)
