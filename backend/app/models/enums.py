from enum import Enum


class TransactionType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


class TransactionSource(str, Enum):
    SMS = "sms"
    RECEIPT = "receipt"
    MANUAL = "manual"
    SYNTHETIC = "synthetic"


DEFAULT_CATEGORIES: list[tuple[str, str, bool]] = [
    ("Food", "food", False),
    ("Groceries", "groceries", False),
    ("Transport", "transport", False),
    ("Shopping", "shopping", False),
    ("Entertainment", "entertainment", False),
    ("Bills", "bills", False),
    ("Utilities", "utilities", False),
    ("Healthcare", "healthcare", False),
    ("Education", "education", False),
    ("Subscriptions", "subscriptions", False),
    ("Travel", "travel", False),
    ("Rent", "rent", False),
    ("Salary/Income", "salary_income", True),
    ("Other", "other", False),
]
