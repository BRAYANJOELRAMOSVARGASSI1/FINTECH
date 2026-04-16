"""
schemas/valuation.py — Pydantic v2 schemas para valoración financiera.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from app.schemas.common import FinEngineBaseModel


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class NPVRequest(FinEngineBaseModel):
    """Solicitud de cálculo de VPN."""

    cash_flows: list[float] = Field(
        ...,
        min_length=2,
        max_length=100,
        description=(
            "Flujos de caja del proyecto. Índice 0 = inversión inicial (negativo). "
            "Ejemplo: [-100000, 30000, 40000, 50000]"
        ),
    )
    discount_rate: float = Field(
        ...,
        gt=-1.0,
        lt=10.0,
        description="Tasa de descuento por período (decimal). Típicamente WACC.",
    )


class IRRRequest(FinEngineBaseModel):
    """Solicitud de cálculo de TIR."""

    cash_flows: list[float] = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Flujos de caja. Debe haber al menos un cambio de signo.",
    )
    hurdle_rate: float | None = Field(
        default=None,
        gt=-1.0,
        lt=10.0,
        description="Tasa mínima requerida (WACC) para emitir decisión.",
    )


class FCFRequest(FinEngineBaseModel):
    """Solicitud de cálculo de Flujo de Caja Libre."""

    revenue: list[float] = Field(..., min_length=1, description="Ingresos por período.")
    operating_expenses: list[float] = Field(..., min_length=1, description="OpEx por período.")
    capex: list[float] = Field(..., min_length=1, description="CapEx por período.")
    tax_rate: float = Field(..., ge=0, lt=1, description="Tasa impositiva.")
    depreciation: list[float] = Field(..., min_length=1, description="Depreciación por período.")
    working_capital_changes: list[float] | None = Field(
        default=None, description="Cambios en capital de trabajo."
    )

    @field_validator("operating_expenses", "capex", "depreciation")
    @classmethod
    def validate_same_length(cls, v: list[float], info) -> list[float]:
        """Las listas se validan en el endpoint contra revenue."""
        return v


class FullValuationRequest(FinEngineBaseModel):
    """Solicitud de valoración completa (VPN + TIR + Payback + PI)."""

    cash_flows: list[float] = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Flujos de caja del proyecto.",
    )
    discount_rate: float = Field(
        ...,
        gt=-1.0,
        lt=10.0,
        description="Tasa de descuento (WACC).",
    )
    hurdle_rate: float | None = Field(
        default=None,
        description="Tasa mínima para TIR. Default = discount_rate.",
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class NPVResponse(FinEngineBaseModel):
    """Resultado del VPN."""

    npv: float
    npv_formatted: str
    discount_rate: float
    periods: int
    decision: str
    present_values: list[float]
    explanation: str


class IRRResponse(FinEngineBaseModel):
    """Resultado de la TIR."""

    irr: float | None
    irr_pct: float | None
    converged: bool
    hurdle_rate: float | None
    decision: str | None
    explanation: str


class PaybackResponse(FinEngineBaseModel):
    """Resultado del payback."""

    simple_payback: float | None
    discounted_payback: float | None
    discount_rate: float
    cumulative_flows: list[float]
    cumulative_pv_flows: list[float]


class ProfitabilityIndexResponse(FinEngineBaseModel):
    """Resultado del índice de rentabilidad."""

    pi: float
    decision: str


class FCFResponse(FinEngineBaseModel):
    """Resultado del FCF."""

    free_cash_flows: list[float]
    total_fcf: float
    periods: int


class FullValuationResponse(FinEngineBaseModel):
    """Resultado de la valoración completa."""

    npv: NPVResponse
    irr: IRRResponse
    payback: PaybackResponse
    profitability_index: ProfitabilityIndexResponse
    cash_flows: list[float]
    discount_rate: float
    overall_recommendation: str
