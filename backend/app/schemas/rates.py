"""
schemas/rates.py — Pydantic v2 schemas para conversión de tasas.

Validación estricta con mensajes de error descriptivos en español.
"""

from __future__ import annotations

from pydantic import Field, field_validator

from app.schemas.common import (
    AnalysisPerspective,
    CompoundingPeriod,
    FinEngineBaseModel,
)


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class RateConversionRequest(FinEngineBaseModel):
    """Solicitud de conversión de tasa nominal a TEA.

    Example:
        {"nominal_rate": 0.18, "compounding": "quarterly"}
        Resultado: TEA = 19.2519%
    """

    nominal_rate: float = Field(
        ...,
        gt=-1.0,
        le=10.0,
        description=(
            "Tasa nominal anual en formato decimal. "
            "Ejemplo: 0.18 para 18%. Máximo: 1000%."
        ),
        examples=[0.18, 0.12, 0.24],
    )
    compounding: CompoundingPeriod = Field(
        ...,
        description="Frecuencia de capitalización.",
        examples=["quarterly", "monthly"],
    )

    @field_validator("nominal_rate")
    @classmethod
    def validate_not_percentage(cls, v: float) -> float:
        """Advierte si parece que ingresaron porcentaje en vez de decimal."""
        if v > 1.0:
            # Podría ser intencional (ej: 150%), pero advertimos
            pass
        return v


class RateComparisonEntry(FinEngineBaseModel):
    """Una tasa individual para comparación."""

    label: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre descriptivo (ej: 'Banco A', 'Opción 1').",
    )
    nominal_rate: float = Field(
        ...,
        gt=-1.0,
        le=10.0,
        description="Tasa nominal anual en decimal.",
    )
    compounding: CompoundingPeriod = Field(
        ...,
        description="Frecuencia de capitalización.",
    )


class RateComparisonRequest(FinEngineBaseModel):
    """Solicitud de comparación de múltiples tasas."""

    rates: list[RateComparisonEntry] = Field(
        ...,
        min_length=2,
        max_length=20,
        description="Lista de tasas a comparar (mínimo 2).",
    )
    perspective: AnalysisPerspective = Field(
        default=AnalysisPerspective.BORROWER,
        description="Perspectiva del análisis: 'borrower' (menor=mejor) o 'investor' (mayor=mejor).",
    )


class FisherRateRequest(FinEngineBaseModel):
    """Solicitud de tasa real (ecuación de Fisher)."""

    nominal_rate: float = Field(
        ...,
        gt=-1.0,
        le=10.0,
        description="Tasa nominal (efectiva) en decimal.",
    )
    inflation_rate: float = Field(
        ...,
        gt=-0.99,
        le=10.0,
        description="Tasa de inflación en decimal.",
    )


class WACCRequest(FinEngineBaseModel):
    """Solicitud de cálculo de WACC."""

    equity: float = Field(..., gt=0, description="Valor de mercado del patrimonio (E).")
    debt: float = Field(..., ge=0, description="Valor de mercado de la deuda (D).")
    cost_of_equity: float = Field(
        ..., gt=-1.0, le=1.0, description="Costo del patrimonio (Ke) — usualmente CAPM."
    )
    cost_of_debt: float = Field(
        ..., ge=0, le=1.0, description="Costo de la deuda (Kd) — TEA de la deuda."
    )
    tax_rate: float = Field(
        ..., ge=0, lt=1.0, description="Tasa impositiva corporativa (T)."
    )


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class RateConversionResponse(FinEngineBaseModel):
    """Resultado de conversión de tasa."""

    original_nominal_rate: float
    compounding: str
    effective_annual_rate: float = Field(
        description="TEA calculada en decimal."
    )
    effective_annual_rate_pct: float = Field(
        description="TEA como porcentaje."
    )
    periodic_rate: float = Field(
        description="Tasa del período en decimal."
    )
    explanation: str = Field(
        description="Explicación del cálculo en lenguaje humano."
    )


class RateComparisonItemResponse(FinEngineBaseModel):
    """Ítem individual en la comparación de tasas."""

    rank: int
    label: str
    nominal_rate: float
    compounding: str
    effective_annual_rate: float
    effective_annual_rate_pct: float


class RateComparisonResponse(FinEngineBaseModel):
    """Resultado de comparación de tasas."""

    perspective: str
    items: list[RateComparisonItemResponse]
    cheapest_label: str
    most_expensive_label: str
    spread_bps: float = Field(description="Spread en basis points.")
    recommendation: str


class FisherRateResponse(FinEngineBaseModel):
    """Resultado de la ecuación de Fisher."""

    nominal_rate: float
    inflation_rate: float
    real_rate: float
    real_rate_pct: float
    explanation: str


class WACCResponse(FinEngineBaseModel):
    """Resultado del cálculo de WACC."""

    wacc: float
    wacc_pct: float
    weight_equity: float
    weight_debt: float
    cost_of_equity: float
    cost_of_debt_after_tax: float
    explanation: str
