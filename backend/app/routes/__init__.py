from fastapi import APIRouter

from backend.app.routes.auth import router as auth_router
from backend.app.routes.insights import (
    router_advisor,
    router_anomalies,
    router_dashboard,
    router_forecast,
    router_subscriptions,
)
from backend.app.routes.nlp import router as nlp_router
from backend.app.routes.ocr import router as ocr_router
from backend.app.routes.transactions import router as transactions_router
from backend.app.routes.users import router as users_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(transactions_router)
api_router.include_router(nlp_router)
api_router.include_router(ocr_router)
api_router.include_router(router_forecast)
api_router.include_router(router_anomalies)
api_router.include_router(router_subscriptions)
api_router.include_router(router_advisor)
api_router.include_router(router_dashboard)
