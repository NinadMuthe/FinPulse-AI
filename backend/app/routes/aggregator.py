"""
aggregator.py — APIRouter for the Setu Account Aggregator (AA) Sandbox integration.

Endpoints:
    POST /aa/consent   — Creates a new consent handle with the Setu AA API and
                         returns the redirect URL for the user consent journey.
    POST /aa/webhook   — Receives and validates state-change callbacks from Setu
                         (consent approved / rejected / revoked / expired).

All calls to the Setu API are made asynchronously via ``httpx.AsyncClient``.
Credentials are loaded from the application Settings class and validated on
import.  If credentials are absent the endpoints return HTTP 503.

Reference:
    https://docs.setu.co/data/account-aggregator/api-integration
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import Response

from backend.app.config import get_settings
from backend.app.schemas.aggregator import (
    ConsentCreateRequest,
    ConsentCreateResponse,
    ConsentNotification,
    ConsentStatus,
    WebhookPayload,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_SETU_SANDBOX_BASE = "https://fiu-uat.setu.co"
_CONSENT_PATH = "/v2/consents"


def _get_setu_headers(settings) -> dict[str, str]:
    """Build the authorisation headers required by the Setu AA API."""
    return {
        "x-client-id": settings.SETU_CLIENT_ID,
        "x-client-secret": settings.SETU_CLIENT_SECRET,
        "Content-Type": "application/json",
    }


def _require_credentials(settings) -> None:
    """
    Raise HTTP 503 if Setu credentials are not configured.

    This provides a clear developer error rather than an obscure 401 from
    the upstream Setu API.
    """
    if not all(
        [
            settings.SETU_CLIENT_ID,
            settings.SETU_CLIENT_SECRET,
            settings.SETU_PRODUCT_INSTANCE_ID,
        ]
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Setu Account Aggregator credentials are not configured. "
                "Set SETU_CLIENT_ID, SETU_CLIENT_SECRET, and "
                "SETU_PRODUCT_INSTANCE_ID in your .env file."
            ),
        )


def _build_setu_consent_body(payload: ConsentCreateRequest, settings) -> dict[str, Any]:
    """
    Translate the FinPulse ``ConsentCreateRequest`` into the JSON body that
    the Setu AA v2 Consent API expects.
    """
    cd = payload.consent_detail
    return {
        "consentDetail": {
            "consentStart": cd.data_date_range.from_.isoformat(),
            "consentExpiry": cd.data_date_range.to.isoformat(),
            "consentMode": "STORE",
            "fetchType": cd.fetch_type.value,
            "consentTypes": cd.consent_types,
            "fiTypes": cd.fi_types,
            "DataConsumer": {"id": settings.SETU_CLIENT_ID},
            "Customer": {"id": ""},  # Setu fills this in during the journey
            "Purpose": {
                "code": cd.purpose_code,
                "refUri": "https://api.rebit.org.in/aa/purpose/101.xml",
                "text": "Wealth management and personal finance analytics",
                "Category": {"type": "personal finance"},
            },
            "FIDataRange": {
                "from": cd.data_date_range.from_.isoformat(),
                "to": cd.data_date_range.to.isoformat(),
            },
            "DataLife": {
                "unit": cd.data_life_unit,
                "value": cd.data_life_value,
            },
            "Frequency": {
                "unit": cd.frequency.unit.value,
                "value": cd.frequency.value,
            },
        },
        "redirectUrl": str(payload.redirect_url),
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/consent",
    response_model=ConsentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate an AA consent request",
    response_description="Setu consent ID and the redirect URL for the user journey.",
)
async def create_consent(payload: ConsentCreateRequest) -> ConsentCreateResponse:
    """
    **Initiate a new Account Aggregator consent request via Setu.**

    Forwards a consent object to the Setu AA sandbox and returns the unique
    ``redirect_url`` that your frontend should open for the user to complete
    the consent journey (approve or deny data sharing with their bank).

    **Flow:**

    1. Client POSTs a ``ConsentCreateRequest`` with the desired data parameters
       and the URL Setu should redirect the user back to.
    2. This endpoint calls ``POST /v2/consents`` on the Setu sandbox.
    3. Setu returns a ``consentHandle`` UUID and a redirect URL.
    4. The caller receives the consent ID and redirect URL.
    5. After the user completes the journey, Setu POSTs a status update to
       ``POST /aa/webhook``.

    **Errors:**

    - ``503`` — Setu credentials not configured in environment.
    - ``502`` — Upstream Setu API returned an unexpected error.
    """
    settings = get_settings()
    _require_credentials(settings)

    body = _build_setu_consent_body(payload, settings)
    url = f"{_SETU_SANDBOX_BASE}{_CONSENT_PATH}"

    logger.info("Initiating Setu AA consent request to %s", url)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                url,
                json=body,
                headers=_get_setu_headers(settings),
            )
        except httpx.RequestError as exc:
            logger.exception("Network error calling Setu AA API: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Could not reach the Setu AA API: {exc}",
            ) from exc

    if response.status_code not in (200, 201):
        logger.error(
            "Setu AA API returned %s: %s",
            response.status_code,
            response.text,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Setu AA API error (HTTP {response.status_code}): "
                f"{response.text[:400]}"
            ),
        )

    data = response.json()
    logger.info("Setu consent created: consentId=%s", data.get("consentHandle"))

    return ConsentCreateResponse(
        consent_id=data.get("consentHandle", ""),
        redirect_url=data.get("redirectUrl", ""),
        status=ConsentStatus.PENDING,
    )


@router.post(
    "/webhook",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Receive Setu AA consent state-change callback",
)
async def aa_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks,
    request: Request,
) -> Response:
    """
    **Webhook receiver for Setu Account Aggregator consent state changes.**

    Setu calls this endpoint whenever the status of a consent changes
    (approved, rejected, revoked, paused, or expired).  The payload is
    validated against ``WebhookPayload`` before any processing begins.

    **Setu Webhook verification:**

    In production you should validate the ``x-jws-signature`` header against
    your Setu public key before trusting the payload.  That step is marked as
    a TODO below and should be implemented before going live.

    **Processing is dispatched to a background task so that this endpoint
    returns ``204 No Content`` immediately**, satisfying Setu's 5-second
    acknowledgement window.

    **Consent lifecycle states handled:**

    | Status   | Meaning                                                  |
    |----------|----------------------------------------------------------|
    | ACTIVE   | User approved — data fetch can now be initiated.         |
    | REJECTED | User denied — no data access granted.                    |
    | REVOKED  | User withdrew consent after prior approval.              |
    | EXPIRED  | Consent duration elapsed without user action.            |
    | FAILED   | Setu encountered an internal error during the journey.   |
    """
    # TODO (production): validate x-jws-signature using Setu's public key.
    # signature = request.headers.get("x-jws-signature")
    # _verify_jws(signature, await request.body())

    logger.info(
        "Setu AA webhook received: consentId=%s status=%s txnId=%s",
        payload.notification.consent_id,
        payload.notification.status,
        payload.txn_id,
    )

    background_tasks.add_task(_handle_consent_state_change, payload.notification)

    # Return 204 No Content — body must be empty.
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Background processing
# ---------------------------------------------------------------------------


def _handle_consent_state_change(notification: ConsentNotification) -> None:
    """
    Persist and act on a consent state change received from Setu.

    Currently logs the event.  Extend this function to:
    - Update a ``consents`` database table with the new status.
    - Trigger a data-fetch session when ``status == ACTIVE``.
    - Send a push notification to the mobile app when consent is revoked.
    """
    consent_id = notification.consent_id
    new_status = notification.status

    logger.info(
        "Processing consent state change: consentId=%s → %s",
        consent_id,
        new_status,
    )

    if new_status == ConsentStatus.ACTIVE:
        logger.info(
            "Consent %s is ACTIVE — data fetch can now be initiated.",
            consent_id,
        )
        # TODO: Trigger FI data fetch session via Setu /v2/consents/{id}/data endpoint.

    elif new_status in (ConsentStatus.REVOKED, ConsentStatus.EXPIRED):
        logger.warning(
            "Consent %s is %s — marking as inactive in the database.",
            consent_id,
            new_status,
        )
        # TODO: Update consent record in DB, halt any scheduled data fetches.

    elif new_status == ConsentStatus.FAILED:
        logger.error("Consent %s FAILED — investigate with Setu support.", consent_id)
