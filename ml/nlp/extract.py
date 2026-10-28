"""
Rule-based transaction extraction from banking SMS / OCR text.

Hugging Face NER is optional and used as a supplement when installed.
Do not assume a single SMS template.
"""

from __future__ import annotations

from datetime import datetime
import re

from ml.categories.taxonomy import classify_category

AMOUNT_PATTERNS = [
    re.compile(r"(?:inr|rs\.?|₹)\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)", re.I),
    re.compile(r"([0-9]{1,3}(?:,[0-9]{2,3})+(?:\.[0-9]{1,2})?|[0-9]+\.[0-9]{2})\s*(?:inr|rs\.?)", re.I),
    re.compile(r"(?:debited|credited|spent|paid)\s+(?:with\s+)?(?:inr|rs\.?|₹)?\s*([0-9,]+(?:\.[0-9]{1,2})?)", re.I),
]

MERCHANT_PATTERNS = [
    re.compile(r"\b(?:at|to|towards|from)\s+([A-Za-z][A-Za-z0-9&.'\-\s]{1,40}?)(?:\s+on\b|\s+for\b|\.|$)", re.I),
    re.compile(r"\b(?:upi|vpa)[:\s]+([A-Za-z0-9.\-_]+)@[A-Za-z]+", re.I),
    re.compile(r"\btrf to\s+([A-Za-z][A-Za-z0-9&.'\-\s]{1,40})", re.I),
]

DATE_PATTERNS = [
    (re.compile(r"\b(\d{1,2})[-/]([A-Za-z]{3,9})[-/](\d{2,4})\b"), "%d-%b-%Y"),
    (re.compile(r"\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b"), "%d-%m-%Y"),
    (re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b"), "%Y-%m-%d"),
]

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _parse_amount(text: str) -> float | None:
    for pattern in AMOUNT_PATTERNS:
        match = pattern.search(text)
        if match:
            raw = match.group(1).replace(",", "")
            try:
                value = float(raw)
            except ValueError:
                continue
            if 0 < value < 10_000_000:
                return value
    return None


def _parse_merchant(text: str) -> str | None:
    lowered = text.lower()
    for pattern in MERCHANT_PATTERNS:
        match = pattern.search(text)
        if match:
            merchant = re.sub(r"\s+", " ", match.group(1)).strip(" .,-")
            if merchant and merchant.lower() not in {"inr", "rs", "your", "a/c", "account"}:
                return merchant.title()
    for name in ["swiggy", "zomato", "amazon", "flipkart", "uber", "ola", "netflix", "spotify", "blinkit"]:
        if name in lowered:
            return name.title()
    return None


def _parse_date(text: str) -> str | None:
    for pattern, _fmt in DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        groups = match.groups()
        try:
            if pattern.pattern.startswith(r"\b(\d{4})"):
                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
            elif groups[1].isalpha():
                day = int(groups[0])
                month = MONTHS.get(groups[1].lower(), 0)
                year = int(groups[2])
            else:
                day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
            if year < 100:
                year += 2000
            parsed = datetime(year, month, day)
            return parsed.date().isoformat()
        except (ValueError, TypeError):
            continue
    return None


def _parse_type(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["credited", "received", "refund", "salary"]):
        return "credit"
    return "debit"


def extract_transaction(text: str) -> dict:
    """Extract amount, merchant, date, category, and type from free text."""
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    amount = _parse_amount(cleaned)
    merchant = _parse_merchant(cleaned)
    date = _parse_date(cleaned)
    tx_type = _parse_type(cleaned)
    category = classify_category(merchant, cleaned)
    filled = sum(value is not None for value in (amount, merchant, date))
    confidence = round(0.25 + 0.25 * filled, 2)
    if amount is None:
        confidence = min(confidence, 0.4)

    hf_entities = _optional_hf_entities(cleaned)
    if hf_entities.get("merchant") and not merchant:
        merchant = hf_entities["merchant"]
        confidence = min(1.0, confidence + 0.1)

    return {
        "amount": amount,
        "merchant": merchant or "Unknown",
        "date": date,
        "category": category,
        "transaction_type": tx_type,
        "confidence_score": confidence,
        "raw_text": cleaned,
    }


def _optional_hf_entities(text: str) -> dict:
    """Best-effort Hugging Face NER. Failures must not break extraction."""
    try:
        from transformers import pipeline  # type: ignore
    except Exception:
        return {}
    try:
        ner = pipeline("ner", grouped_entities=True)
        entities = ner(text)
    except Exception:
        return {}
    org = next((e["word"] for e in entities if e.get("entity_group") in {"ORG", "PER"}), None)
    return {"merchant": org}
