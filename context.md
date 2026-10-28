# FinPulse AI — Project Context & Engineering Blueprint

> **Academic Title:** An AI-Driven Personal Financial Forecasting and Anomaly Detection Framework Using NLP and Time-Series Analysis  
> **Domain:** Computer Science & Engineering — Artificial Intelligence / Machine Learning (B.Tech Final Year Capstone)  
> **Repository Root:** `FinPulse-AI`  
> **Last Updated:** October 2026  

---

## 1. Executive Summary & Problem Formulation

### 1.1 Problem Statement
Young professionals and urban earners frequently encounter month-end liquidity crunches, unexpected subscription renewals, and accidental duplicate charges. Traditional budgeting applications operate **reactively** — classifying historical expenditures after cash is spent without providing forward-looking foresight or risk warnings.

### 1.2 Proposed Solution
**FinPulse AI** bridges this gap by shifting personal accounting from retrospective logging to **predictive financial intelligence**. The platform ingests multi-channel transaction signals (banking SMS alerts, physical receipt scans via OCR, and manual inputs) and feeds them into a pipeline of machine learning models and deterministic heuristics:
- **Forward Spend & Liquidity Forecasting:** 15–30 day expenditure projection using a PyTorch Long Short-Term Memory (LSTM) network benchmarked against Moving Average and Seasonal Naive baselines.
- **Cash Shortfall Warnings:** Automatic reconciliation of predicted spend against liquid bank balances and recurring obligations.
- **Statistical Anomaly Detection:** Scikit-Learn Isolation Forest identifying unusual spending surges.
- **Pattern Heuristics:** Millisecond-to-hour timestamp clustering for duplicate debit detection, and 30-day interval clustering for recurring subscription discovery.
- **Grounded Conversational Advisor:** A LangChain-orchestrated LLM (Google Gemini / OpenAI) strictly grounded on verified application JSON context with zero hallucination allowances and fallback deterministic guidance.

---

## 2. System Architecture

```
                       ┌────────────────────────────────────────┐
                       │        Client Presentation Layer       │
                       │  • React Native Mobile (Expo / Android)│
                       │  • Glassmorphic Web Dashboard (HTML/JS)│
                       └───────────────────┬────────────────────┘
                                           │ HTTP / JSON
                                           ▼
                       ┌────────────────────────────────────────┐
                       │         FastAPI Backend Gateway        │
                       │  (CORS, JWT Auth, Pydantic Validation) │
                       └─────┬────────────────────────────┬─────┘
                             │                            │
            ┌────────────────┴───────────────┐            │
            ▼                                ▼            ▼
┌────────────────────────┐      ┌────────────────────────┐  ┌───────────────────────┐
│  Ingestion & Extraction│      │ ML Intelligence Engine │  │ Persistence Layer     │
├────────────────────────┤      ├────────────────────────┤  ├───────────────────────┤
│ • Regex + HF Token NER │      │ • LSTM Forecasting    │  │ • SQLite (Dev fallback│
│ • EasyOCR Receipt Pipe │      │ • Moving Avg Baseline  │  │ • PostgreSQL (Prod)   │
│ • Category Taxonomy    │      │ • Isolation Forest     │  │ • SQLAlchemy 2.0 ORM  │
└────────────────────────┘      │ • Duplicate/Sub Engine │  │ • Alembic Migrations  │
                                │ • LangChain Advisory   │  └───────────────────────┘
                                └────────────────────────┘
```

---

## 3. Technology Stack & Key Libraries

| Domain / Layer | Technology / Framework | Purpose |
| :--- | :--- | :--- |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11) | High-performance asynchronous REST API framework |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | Production-grade ASGI web server |
| **Database & ORM** | [PostgreSQL](https://www.postgresql.org/) / [SQLite](https://www.sqlite.org/), [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Relational storage and ORM layer |
| **Migrations** | [Alembic](https://alembic.sqlalchemy.org/) | Database schema migration management |
| **Config & Validation**| [Pydantic v2](https://docs.pydantic.dev/), `pydantic-settings` | Schema validation and typed `.env` management |
| **Security & Auth** | `PyJWT`, `passlib[bcrypt]` | Stateless JWT authentication and password hashing |
| **Time-Series ML** | [PyTorch](https://pytorch.org/) (`torch`), [NumPy](https://numpy.org/), [Pandas](https://pandas.pydata.org/) | LSTM neural networks for daily expenditure forecasting |
| **Anomaly Detection** | [scikit-learn](https://scikit-learn.org/) (`IsolationForest`) | Multi-feature statistical spending anomaly isolation |
| **NLP & Entity Extr.** | Python Regex engine, Hugging Face `transformers` | Extract amount, merchant, date, and type from unformatted SMS |
| **Computer Vision/OCR**| [EasyOCR](https://github.com/JaidedAI/EasyOCR), `Pillow` | Text extraction from uploaded physical transaction receipts |
| **AI Advisory Agent** | [LangChain](https://www.langchain.com/), `langchain-google-genai` / `langchain-openai` | Grounded conversational financial advisory layer |
| **Mobile Client** | [React Native](https://reactnative.dev/), [Expo](https://expo.dev/) (SDK 51) | Cross-platform mobile client for Android/iOS |
| **Web Dashboard** | Vanilla HTML5, CSS3 Glassmorphism, [Chart.js](https://www.chartjs.org/) | Responsive real-time administrative and demonstration portal |
| **Testing Suite** | `pytest`, `httpx` (FastAPI TestClient) | Unit, integration, and ML regression test execution |

---

## 4. Repository Structure & Directory Map

```
FinPulse-AI/
├── .env.example                     # Environment template (JWT keys, DB URL, LLM credentials)
├── pyproject.toml                   # Pytest testpaths and formatting configuration
├── README.md                        # Academic overview, installation, and roadmap
├── context.md                       # This comprehensive engineering blueprint
│
├── backend/                         # FastAPI Application Core
│   ├── requirements.txt             # Primary backend and data science dependencies
│   ├── app/
│   │   ├── main.py                  # App entry point, CORS, lifespan handler, routes mount
│   │   ├── config.py                # Pydantic Settings class loading from .env
│   │   ├── database/
│   │   │   ├── base.py              # DeclarativeBase base class for SQLAlchemy models
│   │   │   └── session.py           # Engine & SessionLocal setup (SQLite dev / Postgres prod)
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py              # User entity (auth, credentials, current balance)
│   │   │   ├── transaction.py       # Transaction entity (amount, date, merchant, category)
│   │   │   ├── ml_artifacts.py      # Persisted Forecasts, Anomalies, Subscriptions, Chats
│   │   │   ├── category.py          # Category taxonomy model
│   │   │   └── enums.py             # TransactionType, SourceType, Category enums
│   │   ├── schemas/                 # Pydantic request / response contracts
│   │   │   ├── auth.py              # User registration, login, and token models
│   │   │   ├── transaction.py       # Transaction CRUD, SMS ingestion, extraction schemas
│   │   │   └── ml.py                # ForecastOut, AnomalyOut, SubscriptionOut, ChatRequest
│   │   ├── routes/                  # API Routers
│   │   │   ├── auth.py              # /auth/register, /auth/login
│   │   │   ├── users.py             # /users/me, profile queries
│   │   │   ├── transactions.py      # /transactions (CRUD operations)
│   │   │   ├── nlp.py               # /nlp/extract (SMS text parsing)
│   │   │   ├── ocr.py               # /ocr/receipt (Multipart file OCR parsing)
│   │   │   └── insights.py          # /forecast, /anomalies, /subscriptions, /advisor, /dashboard
│   │   ├── services/                # Business logic
│   │   │   ├── advisor.py           # Grounded LLM advisory & deterministic fallback
│   │   │   ├── liquidity.py         # Balance shortfall calculation & advisory disclaimers
│   │   │   ├── transactions.py      # Transaction querying, list, and formatting
│   │   │   └── categories.py        # Default category seeding
│   │   ├── static/
│   │   │   └── index.html           # Full interactive glassmorphic web dashboard
│   │   └── utils/
│   │       ├── deps.py              # FastAPI auth dependencies (get_current_user)
│   │       └── security.py          # Bcrypt hashing and JWT encoding/decoding
│   └── tests/
│       ├── test_root.py             # Root & health endpoint tests
│       └── test_full_system.py      # End-to-end integration test validating all 20 phases
│
├── ml/                              # Machine Learning & Algorithmic Modules
│   ├── categories/
│   │   └── taxonomy.py              # Merchant-to-category keyword heuristic classifier
│   ├── nlp/
│   │   └── extract.py               # Multi-pattern regex & NER parser for banking SMS
│   ├── ocr/
│   │   └── receipt.py               # EasyOCR image text extractor with confidence scores
│   ├── forecasting/
│   │   ├── lstm_model.py            # PyTorch SpendLSTM neural network definition & training
│   │   ├── baseline.py              # Moving Average & Seasonal Naive benchmark models
│   │   └── pipeline.py              # End-to-end forecasting pipeline with auto-fallback
│   ├── anomaly_detection/
│   │   ├── isolation.py             # Scikit-learn IsolationForest statistical anomaly detector
│   │   ├── duplicates.py            # Deterministic ±1% amount & <=2hr duplicate debit matcher
│   │   └── subscriptions.py         # Timestamp delta clustering (25-35 day interval finder)
│   ├── preprocessing/
│   │   ├── timeseries.py            # Chronological splitting, sliding window, min-max scaling
│   │   └── generate_dataset.py      # Synthetic Indian banking transaction generator (180 days)
│   ├── evaluation/
│   │   └── metrics.py               # MAE, RMSE, and MAPE regression metric calculators
│   └── models/                      # Serialized ML model artifacts (.pt, .json)
│
├── mobile/                          # React Native (Expo) Mobile Client
│   ├── package.json                 # Mobile dependencies (React 18, React Native 0.74, Expo 51)
│   └── App.js                       # Mobile app UI with Dashboard, SMS, Anomalies, Advisor tabs
│
├── database/                        # Database Assets
│   ├── migrations/                  # Alembic versions
│   └── seeds/
│       └── seed_demo.py             # Automated seed script populating demo user & history
│
├── datasets/                        # Dataset Assets
│   ├── raw/                         # Raw synthesized CSVs (transactions.csv)
│   ├── processed/                   # Processed datasets for model training
│   └── README.md                    # Data governance and zero-PII commitment statement
│
├── docs/                            # Formal Documentation
│   └── architecture/
│       └── system_architecture.md   # Architectural reference and defense points
│
└── notebooks/                       # Jupyter Research Notebooks
    ├── exploratory_analysis/
    ├── forecasting/
    ├── anomaly_detection/
    └── nlp/
```

---

## 5. Machine Learning & Analytical Methodologies

### 5.1 NLP Ingestion Pipeline (`ml/nlp/extract.py`)
- **Objective:** Convert unformatted banking SMS notifications into typed transactional records (`amount`, `merchant`, `date`, `category`, `type`).
- **Logic:** Multi-pattern deterministic regular expressions handling diverse Indian banking formats (UPI, NEFT, IMPS, Card Debits) paired with fallback NER.
- **Confidence Scoring:** Dynamically computed between `0.25` and `1.0` based on entity completeness.

### 5.2 Time-Series Expenditure Forecasting (`ml/forecasting/`)
- **Objective:** Forecast daily expenditure over a forward-looking 15 to 30-day horizon.
- **Model:** PyTorch recurrent neural network (`SpendLSTM`) with a linear prediction head trained on rolling sliding windows ($W=14$).
- **Anti-Leakage Guarantee:** Enforces strict chronological data splitting (`chronological_split`: 70% train, 15% validation, 15% test). Shuffling is strictly disallowed to prevent lookahead bias.
- **Benchmarking:** Every forecast is systematically evaluated against a 7-day Moving Average baseline and a Seasonal Naive model using Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Absolute Percentage Error (MAPE).

### 5.3 Statistical Anomaly Detection (`ml/anomaly_detection/isolation.py`)
- **Objective:** Detect statistically aberrant expenditure spikes without falsely classifying them as financial fraud.
- **Model:** Scikit-Learn `IsolationForest(contamination=0.08, random_state=42)`.
- **Feature Vector:** Normalized transaction amount, hour of day, day of week, standard-deviation z-score, and merchant rarity.

### 5.4 Duplicate & Subscription Detection (`ml/anomaly_detection/`)
- **Near-Duplicate Matcher (`duplicates.py`):** Identifies potential billing errors using deterministic constraints: identical merchant, transaction amounts within $\pm 1\%$ tolerance, and timestamps within $\le 2$ hours of each other.
- **Subscription Discovery (`subscriptions.py`):** Evaluates debit history across each merchant. Groups transactions by interval delta and identifies recurring cycles ($25 \le \Delta t \le 35$ days) with low standard deviation to compute confidence scores.

### 5.5 Grounded Conversational Advisor (`backend/app/services/advisor.py`)
- **Principle of Zero Data Fabrication:** The LLM receives a strictly verified JSON context containing balance, projected spend, recurring commitments, and anomalies.
- **Model Grounding:** Prompt engineered to strictly prohibit hallucinating balances or transactions.
- **Deterministic Fallback:** If API keys (`GOOGLE_API_KEY` or `OPENAI_API_KEY`) are omitted, the system seamlessly responds using a rule-based deterministic summary.
- **Mandatory Disclaimers:** Every advisory message contains explicit non-binding financial guidance notices.

---

## 6. API Endpoint Directory

All endpoints are served with automatic interactive OpenAPI documentation at `/docs` and ReDoc at `/redoc`.

| Method | Path | Tag | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root | Serves Web Dashboard for browsers, JSON metadata for API clients |
| `GET` | `/dashboard` | Root | Explicit browser endpoint for the Glassmorphic Dashboard |
| `GET` | `/health` | Health | Health check endpoint returning `{"status": "healthy"}` |
| `POST` | `/auth/register` | Auth | Register a new user account with initial balance |
| `POST` | `/auth/login` | Auth | Authenticate credentials and receive a JWT bearer token |
| `GET` | `/users/me` | Users | Retrieve authenticated user profile |
| `GET` | `/transactions` | Transactions | List transaction history for authenticated user |
| `POST` | `/transactions` | Transactions | Create a single transaction record |
| `GET` | `/transactions/{id}` | Transactions | Retrieve specific transaction details |
| `PATCH` | `/transactions/{id}`| Transactions | Partially update an existing transaction |
| `DELETE`| `/transactions/{id}`| Transactions | Delete a transaction record |
| `POST` | `/nlp/extract` | NLP | Extract structured attributes from raw SMS text |
| `POST` | `/ocr/receipt` | OCR | Ingest multipart image and extract transaction data via EasyOCR |
| `GET` | `/forecast` | Forecast | 30-day LSTM/baseline expenditure projection & liquidity status |
| `GET` | `/anomalies` | Anomalies | Retrieve statistical anomalies detected by Isolation Forest |
| `GET` | `/anomalies/duplicates`| Anomalies | Retrieve near-duplicate transaction pairs |
| `GET` | `/subscriptions` | Subscriptions| List detected recurring subscriptions and frequencies |
| `POST` | `/advisor/chat` | Advisor | Query the grounded AI financial advisor |
| `GET` | `/dashboard` (API) | Dashboard | Unified payload for current balance, spend, warnings, & stats |

---

## 7. Data Strategy, Privacy & Governance

1. **No Real PII / Financial Data:** The project maintains a strict zero-PII commitment. No personal banking credentials or statements are stored in Git.
2. **Synthetic Data Engine:** The project includes a dedicated data synthesis generator ([`ml/preprocessing/generate_dataset.py`](file:///c:/Users/Ninad/Projects/FinPulse-AI/ml/preprocessing/generate_dataset.py)) generating 180 days of realistic Indian transaction histories, categorized debits, monthly salary deposits, and calibrated spending anomalies.
3. **Database Portability:** Configured by default to use local zero-setup SQLite (`sqlite:///./backend/finpulse.db`), with immediate switch-over to PostgreSQL via standard SQLAlchemy connection strings in `.env`.

---

## 8. Development Phases & Roadmap

| Phase | Milestone Name | Status | Key Deliverable |
| :---: | :--- | :---: | :--- |
| **1** | Repository & Backend Foundation | ✅ Complete | FastAPI skeleton, Pydantic settings, Pytest setup |
| **2** | Backend Modular Architecture | ✅ Complete | Routers, schemas, models, and service layer separation |
| **3** | Database Models & Engine | ✅ Complete | SQLAlchemy 2.0 ORM schemas for users, txns, and ML artifacts |
| **4** | Transaction CRUD & JWT Auth | ✅ Complete | Full token auth, hashing, and transaction endpoints |
| **5** | Synthetic Dataset Generator | ✅ Complete | Realistic 180-day Indian banking simulation generator |
| **6** | Receipt OCR Pipeline | ✅ Complete | EasyOCR image ingestion and text extraction |
| **7** | NLP / SMS Entity Extraction | ✅ Complete | Multi-pattern regex & NER extraction with confidence scoring |
| **8** | Category Taxonomy & Classification| ✅ Complete | Merchant keyword mapping and category assignment |
| **9** | Time-Series Forecasting | ✅ Complete | PyTorch LSTM model with Moving Average & Seasonal baselines |
| **10**| Liquidity & Cash-Shortfall Alerts | ✅ Complete | Forward-looking balance deduction and runway warnings |
| **11**| Statistical Anomaly Detection | ✅ Complete | Isolation Forest multi-feature outlier detection |
| **12**| Duplicate & Subscription Discovery | ✅ Complete | Timestamp clustering and interval delta heuristics |
| **13**| Grounded Conversational Advisory | ✅ Complete | LangChain + Gemini/GPT integration with strict grounding |
| **14**| React Native Mobile Application | ✅ Complete | Cross-platform Expo UI with 4 main navigation tabs |
| **15**| Web Demonstration Dashboard | ✅ Complete | Glassmorphic UI at `/dashboard` with Chart.js visualization |
| **16**| End-to-End System Testing | ✅ Complete | Comprehensive 127-line automated test suite passing |
| **17**| Seed Data Automation | ✅ Complete | Script to seed database with historical transaction data |
| **18**| Architecture Documentation | ✅ Complete | Academic methodology and architectural blueprint files |
| **19**| Security & Error Hardening | 🔲 In-Progress | Rate limiting, CORS restrictions, token rotation |
| **20**| Production Deployment | 🔲 Planned | Docker containerization, Cloud Run / VPS deployment |

---

## 9. Local Setup & Execution Guide

### 9.1 Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** & npm (for mobile Expo development)
- **Git**

### 9.2 Virtual Environment & Dependencies
```powershell
# Navigate to project root
cd c:\Users\Ninad\Projects\FinPulse-AI

# Create virtual environment
python -m venv .venv

# Activate virtual environment (PowerShell)
.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt
```

### 9.3 Environment Setup
```powershell
# Copy environment template
copy .env.example .env

# Optional: Add GOOGLE_API_KEY in .env for live Gemini chat
```

### 9.4 Generate Synthetic Data & Seed Database
```powershell
# 1. Generate 180-day transaction dataset
python ml\preprocessing\generate_dataset.py

# 2. Seed database with demo user (demo@finpulse.ai / demo) and transaction history
python database\seeds\seed_demo.py
```

### 9.5 Start Backend Server
```powershell
python -m uvicorn backend.app.main:app --reload --port 8000
```
- **Web Dashboard:** Open [http://localhost:8000/dashboard](http://localhost:8000/dashboard) in your browser.
- **Interactive Swagger Docs:** Open [http://localhost:8000/docs](http://localhost:8000/docs).
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health).

### 9.6 Run Test Suite
```powershell
pytest
```

### 9.7 Run Mobile App (Expo)
```powershell
cd mobile
npm install
npx expo start
```

---

## 10. Key Academic Defense & Viva Talking Points

1. **Proactive vs. Reactive Paradigm:**  
   Unlike Mint, YNAB, or traditional banking apps that summarize historical spending, FinPulse AI forecasts 15–30 days into the future, warning users of liquidity shortfalls *before* they occur.
2. **Defensible ML Architecture:**  
   The LSTM forecasting model is not evaluated in isolation; it is benchmarked against Moving Average and Seasonal Naive baselines using standardized regression metrics (MAE, RMSE, MAPE).
3. **Temporal Data Integrity:**  
   Training and validation sets are split strictly chronologically without random shuffling, eliminating temporal data leakage in time-series evaluation.
4. **Statistical Outlier vs. Fraud Clarification:**  
   Isolation Forest detects *unusual spending volume or timing* relative to the user's personal baseline. It is clearly delineated as an informational spending anomaly, not a banking fraud classifier.
5. **Grounded AI Advisory:**  
   The LLM is strictly constrained via system prompt grounding to only discuss numbers present in the injected JSON payload, preventing fabricated account balances and unauthorized investment recommendations.
