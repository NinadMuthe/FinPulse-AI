from fastapi import APIRouter

from backend.app.schemas.transaction import ExtractionResult, SmsIngestRequest
from ml.nlp.extract import extract_transaction

router = APIRouter(prefix="/nlp", tags=["NLP"])


@router.post("/extract", response_model=ExtractionResult)
def extract(payload: SmsIngestRequest) -> ExtractionResult:
    result = extract_transaction(payload.text)
    return ExtractionResult(
        amount=result["amount"],
        merchant=result["merchant"],
        date=result["date"],
        category=result["category"],
        transaction_type=result["transaction_type"],
        confidence_score=result["confidence_score"],
        raw_text=result["raw_text"],
    )
