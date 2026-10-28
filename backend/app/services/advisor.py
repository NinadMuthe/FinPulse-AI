"""Single-LLM advisory layer. The model must not invent transactions or forecasts."""

from __future__ import annotations

import json
import logging

from backend.app.config import get_settings
from backend.app.services.liquidity import DISCLAIMER

logger = logging.getLogger(__name__)


def build_system_context(payload: dict) -> dict:
    return {
        "forecasted_horizon_spend": payload.get("predicted_spend"),
        "current_balance": payload.get("current_balance"),
        "upcoming_recurring_expenses": payload.get("recurring_obligations"),
        "shortfall_amount": payload.get("shortfall_amount"),
        "top_category": payload.get("top_category"),
        "potential_anomalies": payload.get("anomaly_count"),
        "recent_transactions": payload.get("recent_transactions", []),
        "disclaimer": DISCLAIMER,
    }


def deterministic_reply(message: str, context: dict) -> str:
    spend = context.get("forecasted_horizon_spend") or 0
    balance = context.get("current_balance") or 0
    recurring = context.get("upcoming_recurring_expenses") or 0
    shortfall = context.get("shortfall_amount") or 0
    top = context.get("top_category") or "Other"
    anomalies = context.get("potential_anomalies") or 0
    shortfall_clause = (
        f"A projected shortfall of about ₹{shortfall:,.0f} appears in the model output. "
        if shortfall
        else ""
    )
    return (
        f"Using only the application data: current balance is about ₹{balance:,.0f}, "
        f"projected spending is about ₹{spend:,.0f}, and recurring obligations are about ₹{recurring:,.0f}. "
        f"Top category is {top}. There are {anomalies} potentially unusual transaction(s). "
        f"{shortfall_clause}"
        f"Regarding '{message}': treat these figures as estimates. {DISCLAIMER}"
    )


def llm_reply(message: str, context: dict) -> tuple[str, bool]:
    settings = get_settings()
    api_key = settings.GOOGLE_API_KEY if settings.LLM_PROVIDER == "gemini" else settings.OPENAI_API_KEY
    if not api_key:
        return deterministic_reply(message, context), False
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_core.language_models.chat_models import BaseChatModel

        llm = _build_llm(settings)
        if llm is None:
            return deterministic_reply(message, context), False
        system = (
            "You are FinPulse AI's advisory layer. Use ONLY the JSON system data. "
            "Do not invent transactions, balances, or model predictions. "
            "Isolation Forest findings are statistical anomalies, not fraud. "
            "Forecasts are approximate. Include a brief disclaimer."
        )
        result = llm.invoke(
            [
                SystemMessage(content=system),
                HumanMessage(content=f"SYSTEM DATA:\n{json.dumps(context, default=str)}\n\nUSER:\n{message}"),
            ]
        )
        text = result.content if hasattr(result, "content") else str(result)
        return str(text), True
    except Exception:
        logger.exception("LLM advisor failed; using deterministic reply")
        return deterministic_reply(message, context), False


def _build_llm(settings):
    try:
        if settings.LLM_PROVIDER == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=settings.GOOGLE_API_KEY)
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)
    except Exception:
        logger.exception("Could not construct the configured LLM")
        return None
