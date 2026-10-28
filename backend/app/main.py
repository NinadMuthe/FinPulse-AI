"""
main.py — FastAPI application entry point.

This is the root of the FinPulse AI backend. Routers for auth, transactions,
NLP, OCR, forecasting, anomalies, subscriptions, the advisor, and the
Setu Account Aggregator (AA) integration are registered here.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings

from backend.app.database.session import init_db
from backend.app.routes import api_router
from backend.app.routes.aggregator import router as aggregator_router

settings = get_settings()
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FinPulse AI backend starting up — env: %s", settings.APP_ENV)
    init_db()
    yield
    logger.info("FinPulse AI backend shutting down.")


app = FastAPI(
    title="FinPulse AI — Personal Finance Assistant",
    description=(
        "Backend API for an AI-powered personal finance assistant. "
        "Provides transaction ingestion, NLP extraction, LSTM forecasting, "
        "anomaly detection, and a conversational AI advisory layer."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(aggregator_router, prefix="/aa", tags=["Account Aggregator"])



from pathlib import Path
from fastapi import Request
from fastapi.responses import FileResponse

_STATIC_INDEX = Path(__file__).resolve().parent / "static" / "index.html"


@app.get("/", tags=["Root"])
def root(request: Request):
    """Root endpoint — serves Dashboard UI for web browsers and JSON for API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and _STATIC_INDEX.exists():
        return FileResponse(_STATIC_INDEX)
    return {
        "project": "FinPulse AI",
        "message": "Personal Finance Assistant API is running.",
        "version": app.version,
        "environment": settings.APP_ENV,
    }


@app.get("/dashboard", tags=["Root"])
def dashboard_view():
    """Explicit endpoint to view the web dashboard in any browser."""
    return FileResponse(_STATIC_INDEX)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """Health-check endpoint — used by load balancers and monitors."""
    return {"status": "healthy"}
