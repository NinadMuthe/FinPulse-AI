from datetime import datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    merchant: str = Field(default="Unknown", max_length=128)
    category: str = Field(default="Other", max_length=64)
    transaction_date: datetime | None = None
    transaction_type: str = Field(default="debit")
    source: str = Field(default="manual")
    description: str | None = None
    confidence_score: float | None = Field(default=None, ge=0, le=1)


class TransactionUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    merchant: str | None = None
    category: str | None = None
    transaction_date: datetime | None = None
    transaction_type: str | None = None
    description: str | None = None


class TransactionOut(BaseModel):
    id: int
    user_id: int
    amount: float
    merchant: str
    category: str
    transaction_date: datetime
    transaction_type: str
    source: str
    description: str | None
    confidence_score: float | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class SmsIngestRequest(BaseModel):
    text: str = Field(min_length=5)


class ExtractionResult(BaseModel):
    amount: float | None = None
    merchant: str | None = None
    date: str | None = None
    category: str | None = None
    transaction_type: str | None = None
    confidence_score: float = 0.0
    raw_text: str = ""
