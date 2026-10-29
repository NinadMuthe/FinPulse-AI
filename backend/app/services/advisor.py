"""Single-LLM grounded conversational financial advisory layer.

The advisor is strictly grounded on the user's verified JSON context:
current balance, ML spend forecasts, recurring subscriptions, and Isolation Forest anomalies.
Zero data hallucination is permitted.
"""

from __future__ import annotations

import json
import logging

from backend.app.config import get_settings
from backend.app.services.liquidity import DISCLAIMER

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You are FinPulse AI's conversational financial intelligence advisor.
Your role is to assist the user by answering questions about their financial health, liquidity, budget, and transactions.

CRITICAL RULES FOR ZERO HALLUCINATION:
1. Ground every single claim, number, and recommendation STRICTLY on the provided JSON context data.
2. DO NOT invent, assume, or hallucinate transactions, account balances, recurring bills, or forecasting metrics that are not explicitly present in the data.
3. Treat Isolation Forest anomalies as STATISTICAL OUTLIERS (unusual amounts, timing, or merchants), NOT definitive fraud verdicts.
4. Expenditure forecasts and liquidity cushions are probabilistic model estimates, not guaranteed outcomes.
5. If the user asks about something not covered in the data, state clearly that the information is unavailable in their current verified records.
6. Provide concise, actionable, and encouraging personal finance guidance.
7. Always end with or include this disclaimer: "{DISCLAIMER}"
"""


def build_system_context(payload: dict) -> dict:
    """Extract and package verified user state for LLM grounding."""
    return {
        "current_balance": payload.get("current_balance"),
        "forecasted_horizon_spend": payload.get("predicted_spend"),
        "upcoming_recurring_expenses": payload.get("recurring_obligations"),
        "shortfall_amount": payload.get("shortfall_amount"),
        "top_category": payload.get("top_category"),
        "potential_anomalies": payload.get("anomaly_count"),
        "recent_transactions": payload.get("recent_transactions", []),
        "disclaimer": DISCLAIMER,
    }


def deterministic_reply(message: str, context: dict) -> str:
    """Grounded fallback response built strictly from verified numbers."""
    spend = context.get("forecasted_horizon_spend") or 0.0
    balance = context.get("current_balance") or 0.0
    recurring = context.get("upcoming_recurring_expenses") or 0.0
    shortfall = context.get("shortfall_amount") or 0.0
    top = context.get("top_category") or "General"
    anomalies = context.get("potential_anomalies") or 0

    shortfall_text = (
        f"⚠️ Note: A projected shortfall of approximately ₹{shortfall:,.0f} is anticipated over the next 30 days. "
        if shortfall > 0
        else "Your projected 30-day balance remains positive. "
    )

    return (
        f"Based strictly on your verified financial records:\n"
        f"• Available Liquid Balance: ₹{balance:,.2f}\n"
        f"• Projected 30-Day Spending: ₹{spend:,.2f}\n"
        f"• Upcoming Recurring Bills: ₹{recurring:,.2f}\n"
        f"• Top Spending Category: {top}\n"
        f"• Flagged Statistical Outliers: {anomalies}\n\n"
        f"{shortfall_text}"
        f"In response to your query ('{message}'): Prioritize covering committed recurring expenses and review flagged unusual debits.\n\n"
        f"{DISCLAIMER}"
    )


def llm_reply(message: str, context: dict) -> tuple[str, bool]:
    """Generate financial advisory advice using Gemini via LangChain, strictly grounded on verified JSON context."""
    settings = get_settings()
    api_key = settings.GOOGLE_API_KEY if settings.LLM_PROVIDER == "gemini" else settings.OPENAI_API_KEY

    if not api_key:
        return deterministic_reply(message, context), False

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2,
            timeout=5,
            max_retries=0,
        )

        user_prompt = f"VERIFIED USER FINANCIAL CONTEXT (JSON):\n{json.dumps(context, indent=2, default=str)}\n\nUSER QUESTION:\n{message}"

        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])

        reply_text = response.content if hasattr(response, "content") else str(response)
        return str(reply_text).strip(), True
    except Exception as exc:
        logger.warning("Gemini LLM advisor unavailable or timed out (%s); using grounded deterministic response.", exc)
        return deterministic_reply(message, context), False
