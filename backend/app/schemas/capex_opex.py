"""
schemas/capex_opex.py — Pydantic v2 schemas para análisis CAPEX vs OPEX.
"""

from __future__ import annotations

from pydantic import Field, model_validator

from app.schemas.common import DepreciationMethodEnum, DistributionType, FinEngineBaseModel


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class CapexInputSchema(FinEngineBaseModel):
    """Entrada para el análisis CAPEX."""

    initial_investment: float = Field(
        ...,
        gt=0,
        le=1e12,
        description="Inversión inicial del activo (valor positivo).",
        examples=[500000],
    )
    useful_life_years: int = Field(
        ...,
        ge=1,
        le=50,
        description="Vida útil del activo en años.",
        examples=[5, 10],
    )
    salvage_value: float = Field(
        ...,
        ge=0,
        description="Valor de salvamento al final de la vida útil.",
        examples=[50000],
    )
    annual_maintenance: float = Field(
        default=0,
        ge=0,
        description="Costo de mantenimiento anual.",
    )
    tax_rate: float = Field(
        ...,
        ge=0,
        lt=1.0,
        description="Tasa impositiva corporativa (decimal).",
        examples=[0.30, 0.25],
    )
    depreciation_method: DepreciationMethodEnum = Field(
        default=DepreciationMethodEnum.STRAIGHT_LINE,
        description="Método de depreciación.",
    )
    maintenance_growth_rate: float = Field(
        default=0.0,
        ge=-0.5,
        le=1.0,
        description="Crecimiento anual del costo de mantenimiento (decimal).",
    )

    @model_validator(mode="after")
    def validate_salvage_vs_cost(self) -> "CapexInputSchema":
        """El valor de salvamento debe ser menor que la inversión."""
        if self.salvage_value >= self.initial_investment:
            raise ValueError(
                f"salvage_value ({self.salvage_value}) debe ser < "
                f"initial_investment ({self.initial_investment})."
            )
        return self


class OpexInputSchema(FinEngineBaseModel):
    """Entrada para el análisis OPEX."""

    annual_cost: float = Field(
        ...,
        gt=0,
        le=1e12,
        description="Costo anual del servicio/leasing.",
        examples=[120000],
    )
    contract_years: int = Field(
        ...,
        ge=1,
        le=50,
        description="Duración del contrato en años.",
        examples=[5],
    )
    tax_rate: float = Field(
        ...,
        ge=0,
        lt=1.0,
        description="Tasa impositiva corporativa (decimal).",
    )
    inflation_rate: float = Field(
        default=0.0,
        ge=-0.5,
        le=2.0,
        description="Tasa de inflación anual esperada (decimal).",
        examples=[0.03, 0.05],
    )
    setup_cost: float = Field(
        default=0.0,
        ge=0,
        description="Costo inicial de configuración/migración.",
    )


class CapexVsOpexRequest(FinEngineBaseModel):
    """Solicitud de análisis comparativo CAPEX vs OPEX."""

    capex: CapexInputSchema
    opex: OpexInputSchema
    wacc: float = Field(
        ...,
        gt=-1.0,
        lt=1.0,
        description="WACC de la empresa (tasa de descuento).",
        examples=[0.10, 0.12],
    )
    run_sensitivity: bool = Field(
        default=True,
        description="Ejecutar análisis de sensibilidad.",
    )


class MonteCarloVariableSchema(FinEngineBaseModel):
    """Variable estocástica para Monte Carlo."""

    name: str = Field(..., min_length=1, max_length=50)
    base_value: float = Field(..., description="Valor esperado/base.")
    std_dev: float = Field(..., gt=0, description="Desviación estándar.")
    min_value: float | None = Field(default=None, description="Valor mínimo (clamp).")
    max_value: float | None = Field(default=None, description="Valor máximo (clamp).")
    distribution: DistributionType = Field(default=DistributionType.NORMAL)


class MonteCarloRequest(FinEngineBaseModel):
    """Solicitud de simulación Monte Carlo."""

    cash_flows: list[float] = Field(..., min_length=2, max_length=100)
    discount_rate: float = Field(..., gt=-1.0, lt=10.0)
    variables: list[MonteCarloVariableSchema] = Field(..., min_length=1, max_length=10)
    cash_flow_impacts: dict[str, list[int]] = Field(
        ...,
        description="Mapeo variable_name → lista de índices de flujos afectados.",
    )
    iterations: int = Field(default=10000, ge=100, le=100000)
    seed: int | None = Field(default=42, description="Semilla para reproducibilidad.")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class CapexAnalysisResponse(FinEngineBaseModel):
    """Resultado del análisis CAPEX."""

    cash_flows: list[float]
    depreciation_schedule: list[float]
    tax_shields: list[float]
    maintenance_costs: list[float]
    salvage_net_proceeds: float
    total_cost_nominal: float
    npv_cost: float
    year_labels: list[str]


class OpexAnalysisResponse(FinEngineBaseModel):
    """Resultado del análisis OPEX."""

    cash_flows: list[float]
    annual_costs_nominal: list[float]
    tax_savings: list[float]
    total_cost_nominal: float
    npv_cost: float
    year_labels: list[str]


class SensitivityPointResponse(FinEngineBaseModel):
    """Punto de sensibilidad."""

    variable_name: str
    variation_pct: float
    capex_npv: float
    opex_npv: float
    recommendation: str


class CapexVsOpexResponse(FinEngineBaseModel):
    """Resultado completo de la comparación CAPEX vs OPEX."""

    capex: CapexAnalysisResponse
    opex: OpexAnalysisResponse
    npv_advantage: float
    recommendation: str
    explanation: str
    wacc_used: float
    sensitivity: list[SensitivityPointResponse]


class MonteCarloStatsResponse(FinEngineBaseModel):
    """Estadísticas de Monte Carlo."""

    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_5: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    percentile_95: float
    probability_positive: float
    probability_negative: float
    skewness: float
    kurtosis: float


class MonteCarloResponse(FinEngineBaseModel):
    """Resultado completo de Monte Carlo."""

    iterations: int
    stats: MonteCarloStatsResponse
    histogram_bins: list[float]
    histogram_counts: list[int]
    variables_stressed: list[str]
    confidence_interval_90: list[float]
    confidence_interval_95: list[float]
    decision: str
    risk_assessment: str
