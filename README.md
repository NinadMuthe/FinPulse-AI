# FinPulse AI — AI-Powered Personal Finance Assistant

> **Academic Title:** An AI-Driven Personal Financial Forecasting and Anomaly Detection Framework Using NLP and Time-Series Analysis
>
> **Domain:** Computer Science & Engineering — Artificial Intelligence / Machine Learning
>
> **Type:** Final-year B.Tech CSE (AI/ML) Project

---

## Problem Statement

Young earners and metro users frequently face month-end liquidity crises, subscription traps, duplicate charges, and difficulty understanding where their money is going. Existing expense apps are *reactive* — they show past spending but provide no forward-looking intelligence.

## Proposed Solution

FinPulse AI transforms raw transaction data (SMS, receipts, manual entry) into predictive and actionable financial intelligence using:

- **NLP/NER** — automatic extraction from banking SMS
- **EasyOCR + NER** — receipt scanning
- **LSTM** — 15–30 day expenditure & liquidity forecasting
- **Isolation Forest** — anomaly / unusual transaction detection
- **LangChain + LLM** — conversational AI financial advisor

---

## Features

| Feature | Status |
|---------|--------|
| Transaction ingestion (SMS / Receipt / Manual) | 🔲 Planned |
| NLP/NER extraction | 🔲 Planned |
| OCR receipt scanning | 🔲 Planned |
| Category classification | 🔲 Planned |
| LSTM expenditure forecasting | 🔲 Planned |
| Liquidity / cash-shortfall warnings | 🔲 Planned |
| Anomaly detection | 🔲 Planned |
| Duplicate / subscription detection | 🔲 Planned |
| AI financial advisor (LLM) | 🔲 Planned |
| React Native mobile app | 🔲 Planned |
| FastAPI backend ✅ | ✅ Phase 1 |

---

## Architecture

```
React Native App
       │
       ▼
FastAPI Backend ──────────────── PostgreSQL
       │
       ├── NLP / OCR Pipeline
       │         ├── EasyOCR
       │         └── HuggingFace Transformers / NER
       │
       ├── LSTM Forecasting (PyTorch)
       ├── Isolation Forest (scikit-learn)
       └── AI Advisory (LangChain + LLM)
```

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Mobile | React Native (Android) |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Config | pydantic-settings, python-dotenv |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| OCR | EasyOCR |
| NLP | Hugging Face Transformers |
| Forecasting | PyTorch LSTM |
| Anomaly Detection | scikit-learn Isolation Forest |
| AI Advisory | LangChain + Google Gemini (single LLM) |
| Testing | pytest, httpx |

---

## Folder Structure

```
FinPulse-AI/
├── backend/
│   ├── app/
│   │   ├── main.py          ← FastAPI app entry point
│   │   ├── config.py        ← Environment-based settings
│   │   ├── database/        ← DB engine & session (Phase 3)
│   │   ├── models/          ← SQLAlchemy ORM models (Phase 3)
│   │   ├── schemas/         ← Pydantic request/response schemas
│   │   ├── routes/          ← API routers
│   │   ├── services/        ← Business logic
│   │   └── utils/           ← Shared utilities
│   ├── tests/               ← pytest test suite
│   └── requirements.txt
├── ml/
│   ├── nlp/                 ← NLP/NER extraction
│   ├── ocr/                 ← EasyOCR pipeline
│   ├── forecasting/         ← LSTM training & inference
│   ├── anomaly_detection/   ← Isolation Forest
│   ├── preprocessing/       ← Data cleaning & feature engineering
│   ├── evaluation/          ← Metrics & comparison scripts
│   └── models/              ← Saved model artifacts (gitignored)
├── mobile/                  ← React Native app
├── database/
│   ├── migrations/          ← Alembic migrations
│   └── seeds/               ← Seed data scripts
├── datasets/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── notebooks/               ← Jupyter exploratory notebooks
├── tests/
│   ├── integration/
│   └── end_to_end/
├── docs/                    ← Architecture, API, ML docs
├── .env.example             ← Environment variable template
├── .gitignore
├── pyproject.toml           ← pytest configuration
├── README.md
└── LICENSE
```

---

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL (Phase 3+)
- Node.js + Expo CLI (Phase 14+)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/FinPulse-AI.git
cd FinPulse-AI
```

### 2. Create and activate the virtual environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install backend dependencies

```powershell
pip install -r backend\requirements.txt
```

### 4. Configure environment variables

```powershell
copy .env.example .env
# Edit .env with your real values
```

### 5. Run the backend server

```powershell
python -m uvicorn backend.app.main:app --reload
```

### 6. Verify endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Root — confirms API is running |
| `GET /health` | Health check |
| `GET /docs` | Swagger UI (interactive API docs) |
| `GET /redoc` | ReDoc API docs |

---

## Running Tests

```powershell
pytest
```

---

## Environment Variables

See [.env.example](.env.example) for the full list of required variables.

> **Never commit `.env` to Git.**

---

## Development Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Repository & backend foundation | ✅ Current |
| 2 | FastAPI backend structure | 🔲 |
| 3 | PostgreSQL database | 🔲 |
| 4 | Transaction CRUD APIs | 🔲 |
| 5 | Synthetic dataset | 🔲 |
| 6 | OCR pipeline | 🔲 |
| 7 | NLP/NER extraction | 🔲 |
| 8 | Category classification | 🔲 |
| 9 | LSTM forecasting | 🔲 |
| 10 | Liquidity warnings | 🔲 |
| 11 | Anomaly detection | 🔲 |
| 12 | Duplicate/subscription detection | 🔲 |
| 13 | AI advisory (LLM) | 🔲 |
| 14 | React Native mobile app | 🔲 |
| 15 | SMS listener & receipt scanner | 🔲 |
| 16 | Full system integration | 🔲 |
| 17 | Testing | 🔲 |
| 18 | Security & error handling | 🔲 |
| 19 | Deployment | 🔲 |
| 20 | Documentation & presentation | 🔲 |

---

## Disclaimer

FinPulse AI provides informational financial guidance only.
It does not constitute professional financial advice.
AI-generated outputs should not be treated as guaranteed financial outcomes.

---

## License

[MIT](LICENSE)
