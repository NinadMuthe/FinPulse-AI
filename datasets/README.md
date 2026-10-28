# Datasets

This folder holds all data assets used by the FinPulse AI ML pipeline.

```
datasets/
├── raw/         ← original, unmodified data (synthetic or real, anonymized)
├── processed/   ← cleaned, feature-engineered data ready for training
└── README.md    ← this file
```

## Data Strategy

Real personal financial data is **never** committed to this repository.

All data used during development is either:
1. **Synthetically generated** using scripts in `ml/preprocessing/`.
2. **Fully anonymised** before being placed here.

## Dataset Schema (target)

| Column            | Type      | Description                              |
|-------------------|-----------|------------------------------------------|
| `date`            | date      | Transaction date                         |
| `amount`          | float     | Transaction amount in INR                |
| `merchant`        | string    | Merchant or counterparty name            |
| `category`        | string    | Spending category (Food, Transport, …)   |
| `transaction_type`| string    | debit / credit                           |
| `source`          | string    | sms / receipt / manual                   |
| `user_id`         | int       | Anonymised user identifier               |
| `description`     | string    | Raw text used for extraction             |
| `balance`         | float     | Running balance after transaction        |

> **Note:** This schema will be finalised in Phase 5 (Synthetic Dataset).
