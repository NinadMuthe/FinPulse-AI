"""
aggregator.py — Pydantic schemas for the Setu Account Aggregator (AA) integration.

Covers:
- ConsentDetailOut : structure of the data request sent to Setu for consent creation.
- ConsentCreateResponse : response returned to the caller after consent creation.
- WebhookPayload   : validated structure of the state-change callback from Setu.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ConsentStatus(str, Enum):
    """Possible consent lifecycle states emitted by the Setu AA platform."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"


class FetchType(str, Enum):
    """Whether data is fetched once or on a recurring schedule."""

    ONE_TIME = "ONE_TIME"
    PERIODIC = "PERIODIC"


class FrequencyUnit(str, Enum):
    """Temporal unit for periodic fetch frequency."""

    HOUR = "HOUR"
    DAY = "DAY"
    MONTH = "MONTH"
    YEAR = "YEAR"


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class Frequency(BaseModel):
    """Recurring data-fetch cadence embedded inside ConsentDetail."""

    unit: FrequencyUnit = FrequencyUnit.MONTH
    value: int = Field(default=1, ge=1, description="Number of units between fetches.")


class DateTimeRange(BaseModel):
    """Inclusive date range for financial data access."""

    from_: date = Field(alias="from", description="Start date (ISO 8601).")
    to: date = Field(description="End date (ISO 8601).")

    model_config = {"populate_by_name": True}


class ConsentDetailOut(BaseModel):
    """
    Data-request payload forwarded to the Setu AA API when creating a new consent.

    Defines *what* financial data is requested, over *what* period, and at
    *what* fetch frequency.  This mirrors the ``consentDetail`` block in the
    Setu Consent Object specification.
    """

    consent_types: list[Literal["ACCOUNT_SUMMARY", "TRANSACTIONS", "PROFILE"]] = Field(
        default=["TRANSACTIONS", "ACCOUNT_SUMMARY"],
        description="Categories of data requested from the user's financial institution.",
    )
    fi_types: list[
        Literal[
            "DEPOSIT",
            "MUTUAL_FUNDS",
            "INSURANCE_POLICIES",
            "TERM_DEPOSIT",
            "RECURRING_DEPOSIT",
            "SIP",
            "GOVT_SECURITIES",
            "EQUITIES",
            "BONDS",
            "DEBENTURES",
            "ETF",
            "IDR",
            "CIS",
            "AIF",
            "FOREX",
            "ESOP",
            "INVITs",
            "REITs",
            "NPS",
            "INVIT",
            "OTHER",
        ]
    ] = Field(
        default=["DEPOSIT"],
        description="Financial instrument types covered by the consent.",
    )
    data_date_range: DateTimeRange = Field(
        description="Inclusive date range for which the user authorises data sharing."
    )
    fetch_type: FetchType = Field(
        default=FetchType.PERIODIC,
        description="Whether data is pulled once or on a recurring schedule.",
    )
    frequency: Frequency = Field(
        default_factory=Frequency,
        description="Applicable only when fetch_type is PERIODIC.",
    )
    data_life_value: int = Field(
        default=1,
        ge=1,
        description="How long (in data_life_unit) the AA may retain fetched data.",
    )
    data_life_unit: Literal["DAY", "MONTH", "YEAR", "INF"] = Field(
        default="MONTH",
        description="Temporal unit for data_life_value.",
    )
    purpose_code: str = Field(
        default="101",
        description=(
            "Setu purpose code. "
            "101 = Wealth management, "
            "102 = Customer spending patterns, etc."
        ),
    )


class ConsentCreateRequest(BaseModel):
    """
    Request body accepted by ``POST /aa/consent``.

    The caller provides a redirect URL and optionally overrides the default
    ConsentDetail parameters.
    """

    redirect_url: HttpUrl = Field(
        description=(
            "URL to which the user is redirected after completing the consent journey "
            "on the Setu AA web interface."
        )
    )
    consent_detail: ConsentDetailOut = Field(
        default_factory=ConsentDetailOut,
        description="Data-request parameters forwarded to Setu.  Defaults are production-safe.",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ConsentCreateResponse(BaseModel):
    """
    Response returned to the client after successfully initiating a consent request
    with the Setu AA API.
    """

    consent_id: str = Field(description="Unique Setu-issued consent identifier (UUID).")
    redirect_url: str = Field(
        description="URL to redirect the user to for completing the consent journey."
    )
    status: ConsentStatus = Field(description="Initial lifecycle status of the consent.")


# ---------------------------------------------------------------------------
# Webhook schemas
# ---------------------------------------------------------------------------


class ConsentNotification(BaseModel):
    """Minimal notification block inside a Setu webhook payload."""

    consent_id: str = Field(alias="consentId")
    status: ConsentStatus
    timestamp: datetime

    model_config = {"populate_by_name": True}


class WebhookPayload(BaseModel):
    """
    Validated structure of the state-change callback POSTed by Setu to
    ``POST /aa/webhook``.

    Setu sends this when a user approves, rejects, revokes, or when the
    consent expires.  Only the fields relevant to FinPulse AI are captured;
    additional keys are silently ignored (``extra="ignore"``).

    Reference:
        https://docs.setu.co/data/account-aggregator/api-integration
    """

    ver: str = Field(description="Setu API version string.")
    timestamp: datetime = Field(description="ISO 8601 event timestamp.")
    txn_id: str = Field(alias="txnid", description="Setu transaction / trace ID.")
    notification: ConsentNotification

    model_config = {"populate_by_name": True, "extra": "ignore"}
