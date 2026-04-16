"""
schemas/amortization.py — Pydantic v2 schemas para tablas de amortización.
"""

from __future__ import annotations

from pydantic import Field

from app.schemas.common import AmortizationSystem, FinEngineBaseModel


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class AmortizationRequest(FinEngineBaseModel):
    """Solicitud de generación de tabla de amortización."""

    principal: float = Field(
        ...,
        gt=0,
        le=1e12,
        description="Monto del préstamo.",
        examples=[100000, 500000],
    )
    annual_rate: float = Field(
        ...,
        ge=0,
        le=5.0,
        description="Tasa de interés anual en decimal (ej: 0.12 para 12%).",
        examples=[0.12, 0.18],
    )
    total_periods: int = Field(
        ...,
        ge=1,
        le=600,
        description="Número total de cuotas.",
        examples=[12, 24, 36, 60],
    )
    periods_per_year: int = Field(
        default=12,
        ge=1,
        le=365,
        description="Períodos por año (12=mensual, 4=trimestral, etc.).",
    )
    system: AmortizationSystem = Field(
        ...,
        description="Sistema de amortización: french, german, o american.",
    )


class AmortizationCompareRequest(FinEngineBaseModel):
    """Solicitud de comparación de los tres sistemas."""

    principal: float = Field(..., gt=0, le=1e12)
    annual_rate: float = Field(..., ge=0, le=5.0)
    total_periods: int = Field(..., ge=1, le=600)
    periods_per_year: int = Field(default=12, ge=1, le=365)


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class AmortizationRowResponse(FinEngineBaseModel):
    """Una fila de la tabla de amortización."""

    period: int
    payment: float
    interest: float
    principal: float
    balance: float


class AmortizationTableResponse(FinEngineBaseModel):
    """Tabla completa de amortización."""

    system: str
    principal_amount: float
    annual_rate: float
    annual_rate_pct: float
    periodic_rate: float
    total_periods: int
    total_paid: float
    total_interest: float
    interest_ratio: float
    first_payment: float
    last_payment: float
    rows: list[AmortizationRowResponse]


class AmortizationCompareResponse(FinEngineBaseModel):
    """Comparación de los tres sistemas de amortización."""

    french: AmortizationTableResponse
    german: AmortizationTableResponse
    american: AmortizationTableResponse
    cheapest_system: str
    recommendation: str
