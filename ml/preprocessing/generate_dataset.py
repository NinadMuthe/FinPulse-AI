"""
Synthetic financial transaction generator for FinPulse AI.
Generates realistic Indian UPI/banking transactions for ML benchmarking.
"""

import csv
import datetime
import random
from pathlib import Path

MERCHANTS = {
    "Food": ["Swiggy", "Zomato", "McDonalds", "Chai Point", "Starbucks", "Dominos"],
    "Groceries": ["Blinkit", "Zepto", "Instamart", "BigBasket", "DMart"],
    "Transport": ["Uber", "Ola", "Metro Rail", "Rapido", "Petrol Pump"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Zara", "Decathlon"],
    "Entertainment": ["Netflix", "Spotify", "BookMyShow", "PVR Cinemas"],
    "Bills": ["BESCOM", "Airtel", "Jio", "Indane Gas", "Water Supply"],
    "Healthcare": ["Apollo Pharmacy", "1mg", "Practo", "Cult.fit"],
    "Salary/Income": ["TechCorp Employer", "Freelance Client", "Dividend Payout"],
}

CATEGORY_WEIGHTS = {
    "Food": 0.30,
    "Groceries": 0.20,
    "Transport": 0.15,
    "Shopping": 0.12,
    "Entertainment": 0.08,
    "Bills": 0.08,
    "Healthcare": 0.05,
    "Salary/Income": 0.02,
}

AMOUNT_RANGES = {
    "Food": (80, 850),
    "Groceries": (200, 2500),
    "Transport": (50, 600),
    "Shopping": (500, 6000),
    "Entertainment": (199, 1200),
    "Bills": (499, 3200),
    "Healthcare": (150, 2000),
    "Salary/Income": (45000, 85000),
}


def generate_synthetic_transactions(num_records: int = 1000, user_id: int = 1, output_file: str = "datasets/raw/transactions.csv") -> Path:
    start_date = datetime.date.today() - datetime.timedelta(days=180)
    current_balance = 35000.0

    categories = list(CATEGORY_WEIGHTS.keys())
    weights = list(CATEGORY_WEIGHTS.values())

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    # Guarantee 1 monthly salary per month
    for month_offset in range(6):
        sal_date = start_date + datetime.timedelta(days=month_offset * 30 + 1)
        sal_amt = 65000.0
        current_balance += sal_amt
        rows.append({
            "date": sal_date.isoformat(),
            "amount": sal_amt,
            "merchant": "TechCorp Solutions",
            "category": "Salary/Income",
            "transaction_type": "credit",
            "source": "sms",
            "user_id": user_id,
            "description": f"A/C credited with INR {sal_amt:.2f} by TechCorp on {sal_date}",
            "balance": round(current_balance, 2),
        })

    # Generate daily expense activity
    for day in range(180):
        current_day = start_date + datetime.timedelta(days=day)
        # 1 to 5 transactions per day
        daily_txns = random.randint(1, 5)
        for _ in range(daily_txns):
            cat = random.choices(categories[:-1], weights=weights[:-1])[0]  # expense categories
            low, high = AMOUNT_RANGES[cat]
            amt = round(random.uniform(low, high), 2)
            merchant = random.choice(MERCHANTS[cat])
            current_balance = max(1000.0, current_balance - amt)

            rows.append({
                "date": current_day.isoformat(),
                "amount": amt,
                "merchant": merchant,
                "category": cat,
                "transaction_type": "debit",
                "source": random.choice(["sms", "sms", "manual", "receipt"]),
                "user_id": user_id,
                "description": f"Paid INR {amt:.2f} to {merchant} on {current_day}",
                "balance": round(current_balance, 2),
            })

    # Inject 5 unusual spending anomalies (Phase 11 verification)
    anomaly_dates = [start_date + datetime.timedelta(days=d) for d in [25, 60, 95, 130, 165]]
    for ad in anomaly_dates:
        amt = round(random.uniform(18000, 32000), 2)
        rows.append({
            "date": ad.isoformat(),
            "amount": amt,
            "merchant": "Luxury Watch Boutique",
            "category": "Shopping",
            "transaction_type": "debit",
            "source": "sms",
            "user_id": user_id,
            "description": f"Txn of INR {amt:.2f} at Luxury Watch Boutique on {ad}",
            "balance": round(current_balance, 2),
        })

    # Sort chronologically
    rows.sort(key=lambda r: r["date"])

    with open(out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return out_path


if __name__ == "__main__":
    p = generate_synthetic_transactions()
    print(f"Generated synthetic transactions at {p}")
