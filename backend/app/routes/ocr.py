from fastapi import APIRouter, File, HTTPException, UploadFile
import tempfile
from pathlib import Path

from ml.nlp.extract import extract_transaction

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/receipt")
async def receipt(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "receipt.png").suffix or ".png"
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Empty upload")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    try:
        from ml.ocr.receipt import receipt_to_transaction

        return receipt_to_transaction(tmp_path)
    except ImportError:
        text = contents.decode("utf-8", errors="ignore")
        if not text.strip():
            raise HTTPException(
                status_code=503,
                detail="EasyOCR is not installed. Install backend/requirements-ml.txt to enable receipt OCR.",
            )
        extracted = extract_transaction(text)
        extracted["source"] = "receipt"
        extracted["ocr_confidence"] = None
        return extracted
