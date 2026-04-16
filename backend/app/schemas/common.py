"""
schemas/common.py — Tipos compartidos, enums y modelos base.

Define los tipos fundamentales que se reutilizan en todos
los schemas del sistema. Actúa como el "vocabulario" de la API.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Enums — Vocabulario unificado del sistema
# ---------------------------------------------------------------------------


class CompoundingPeriod(str, Enum):
    """Frecuencias de capitalización soportadas."""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    BIMONTHLY = "bimonthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"
    CONTINUOUS = "continuous"


class DepreciationMethodEnum(str, Enum):
    """Métodos de depreciación disponibles."""

    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    SUM_OF_YEARS_DIGITS = "sum_of_years_digits"


class AmortizationSystem(str, Enum):
    """Sistemas de amortización de deuda."""

    FRENCH = "french"
    GERMAN = "german"
    AMERICAN = "american"


class AnalysisPerspective(str, Enum):
    """Perspectiva del análisis de tasas."""

    BORROWER = "borrower"  # Menor TEA = mejor
    INVESTOR = "investor"  # Mayor TEA = mejor


class RiskDecision(str, Enum):
    """Clasificación de riesgo del Monte Carlo."""

    HIGH_CONFIDENCE_ACCEPT = "HIGH_CONFIDENCE_ACCEPT"
    MODERATE_RISK = "MODERATE_RISK"
    HIGH_RISK_REJECT = "HIGH_RISK_REJECT"


class DistributionType(str, Enum):
    """Tipos de distribución para Monte Carlo."""

    NORMAL = "normal"
    TRIANGULAR = "triangular"
    UNIFORM = "uniform"


# ---------------------------------------------------------------------------
# Base Models
# ---------------------------------------------------------------------------


class FinEngineBaseModel(BaseModel):
    """Modelo base para todos los schemas de FinEngine.

    Configuración compartida:
    - Modo estricto de validación
    - Serialización consistente
    - Documentación de ejemplo en OpenAPI
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        from_attributes=True,
    )


class HealthResponse(FinEngineBaseModel):
    """Respuesta del health check."""

    status: str = "healthy"
    version: str
    engine: str = "FinEngine"


class ErrorResponse(FinEngineBaseModel):
    """Respuesta de error estandarizada."""

    error: str
    detail: str
    status_code: int
