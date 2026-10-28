"""Configurable spending categories and merchant keyword map."""

from backend.app.models.enums import DEFAULT_CATEGORIES

CATEGORY_NAMES = [name for name, _slug, _income in DEFAULT_CATEGORIES]

MERCHANT_KEYWORDS: dict[str, list[str]] = {
    "Food": ["swiggy", "zomato", "dominos", "mcdonald", "kfc", "starbucks", "cafe", "restaurant", "eats"],
    "Groceries": ["blinkit", "zepto", "bigbasket", "dmart", "reliance fresh", "grocery", "supermarket"],
    "Transport": ["uber", "ola", "rapido", "irctc", "metro", "petrol", "fuel", "parking"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "meesho", "nykaa"],
    "Entertainment": ["netflix", "spotify", "bookmyshow", "hotstar", "prime video", "youtube"],
    "Bills": ["airtel", "jio", "vi ", "bsnl", "recharge"],
    "Utilities": ["electricity", "bescom", "mseb", "water board", "gas"],
    "Healthcare": ["apollo", "pharmeasy", "1mg", "practo", "hospital", "pharmacy"],
    "Education": ["udemy", "coursera", "byju", "unacademy", "school", "college"],
    "Subscriptions": ["netflix", "spotify", "youtube premium", "icloud", "google one", "adobe"],
    "Travel": ["makemytrip", "goibibo", "airbnb", "indigo", "air india", "hotel"],
    "Rent": ["rent", "landlord", "nobroker"],
    "Salary/Income": ["salary", "payroll", "credited by", "neft cr"],
}


def classify_category(merchant: str | None, text: str = "") -> str:
    haystack = f"{merchant or ''} {text}".lower()
    for category, keywords in MERCHANT_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return category
    if any(word in haystack for word in ["salary", "credited", "refund"]):
        return "Salary/Income"
    return "Other"
