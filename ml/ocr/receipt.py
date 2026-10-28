"""Receipt OCR pipeline. EasyOCR is loaded lazily and may be unavailable in tests."""

from __future__ import annotations

from pathlib import Path

from ml.nlp.extract import extract_transaction

_READER = None


def _get_reader():
    global _READER
    if _READER is None:
        import easyocr  # type: ignore

        _READER = easyocr.Reader(["en"], gpu=False)
    return _READER


def extract_text_from_image(image_path: str | Path) -> tuple[str, float]:
    reader = _get_reader()
    results = reader.readtext(str(image_path))
    if not results:
        return "", 0.0
    texts = [item[1] for item in results]
    confidences = [float(item[2]) for item in results]
    avg_conf = sum(confidences) / len(confidences)
    return " ".join(texts), round(avg_conf, 3)


def receipt_to_transaction(image_path: str | Path) -> dict:
    text, ocr_confidence = extract_text_from_image(image_path)
    extracted = extract_transaction(text)
    extracted["ocr_confidence"] = ocr_confidence
    extracted["source"] = "receipt"
    extracted["confidence_score"] = round(
        0.5 * extracted["confidence_score"] + 0.5 * ocr_confidence, 3
    )
    return extracted
