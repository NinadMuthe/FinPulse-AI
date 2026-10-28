# FinPulse AI — Architecture & Methodology Reference

**Academic Title:** An AI-Driven Personal Financial Forecasting and Anomaly Detection Framework Using NLP and Time-Series Analysis  
**Project Domain:** Computer Science & Engineering — Artificial Intelligence / Machine Learning (B.Tech Final Year)

---

## 1. System Overview
FinPulse AI is a predictive personal finance platform that shifts personal accounting from reactive tracking to proactive intelligence.

```
React Native Client (Mobile)
          │
          ▼
   FastAPI Gateway
   ├── Ingestion Pipeline (SMS / Receipts / Manual)
   ├── NLP Entity Extraction (Regex + Transformers)
   ├── OCR Processing (EasyOCR)
   ├── Relational Store (PostgreSQL / SQLite fallback)
   ├── Forecasting Engine (Moving Average Baseline vs. PyTorch LSTM)
   ├── Anomaly Engine (Scikit-Learn Isolation Forest)
   ├── Rule-Based Heuristics (Duplicate & Subscription Detectors)
   └── Advisory Layer (LangChain + Single LLM)
```

---

## 2. Machine Learning Methodologies

### 2.1 Natural Language Processing (NLP)
* **Objective:** Extract structured records (`amount`, `merchant`, `date`, `category`, `type`) from unformatted banking SMS notifications.
* **Pipeline:** Multi-pattern deterministic extraction combined with Hugging Face token classification (`ner`).
* **Confidence Scoring:** Computed based on extracted entity coverage (0.25 to 1.0).

### 2.2 Time-Series Expenditure Forecasting
* **Objective:** 15–30 day forward-looking daily expenditure projection.
* **Architecture:** PyTorch LSTM recurrent neural network trained on rolling sliding windows ($W=14$).
* **Data Leakage Prevention:** Strict chronological train/validation/test splitting (no random shuffling).
* **Baseline Comparison:** Benchmarked against Moving Average and Seasonal Naive baselines using MAE and RMSE metrics.

### 2.3 Statistical Anomaly Detection
* **Objective:** Identify statistically unusual expenditure spikes without falsely labeling them as fraud.
* **Model:** Scikit-Learn `IsolationForest(contamination=0.03, random_state=42)`.
* **Features:** Transaction amount, category encoding, and rolling baseline deviations.

### 2.4 Duplicate & Subscription Detection
* **Duplicates:** Deterministic matching on identical merchant, close amount ($\pm 1\%$), and timestamp proximity ($\le 2$ hours).
* **Subscriptions:** Interval clustering ($25 \le \Delta t \le 35$ days) with median standard deviation analysis.

### 2.5 Grounded AI Advisory Layer
* **Constraint:** Zero data fabrication. The LLM receives strictly verified JSON system context.
* **Tone:** Informational guidance with explicit financial disclaimers.

---

## 3. Academic Defense Talking Points
1. **Predictive vs. Reactive:** Solves end-of-month cash shortfalls before they occur.
2. **Defensible ML:** LSTM performance is strictly compared against moving-average baselines with verifiable evaluation metrics.
3. **Privacy & Security:** Sensitive SMS parsing occurs with user consent; secrets and credentials are never checked into version control.
