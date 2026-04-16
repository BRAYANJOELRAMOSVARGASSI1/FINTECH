"""
startup.py — Schemas Pydantic para modelos de Venture Capital, Working Capital y Bootstrapping.
"""

from typing import Union
from pydantic import BaseModel, Field

# --- Venture Capital ---

class ConvertibleNoteRequest(BaseModel):
    investment: float = Field(..., gt=0, description="Inversión inicial")
    valuation_cap: float = Field(..., ge=0, description="Tope de valoración")
    discount_rate: float = Field(..., ge=0, lt=1, description="Tasa de descuento")
    next_round_pre_money: float = Field(..., gt=0, description="Valoración Pre-Money en la ronda de conversión")

class ConvertibleNoteResponse(BaseModel):
    investment: float
    cap: float
    discount: float
    next_round_valuation: float
    effective_valuation: float
    investor_ownership_pct: float
    founder_retained_pct: float
    conversion_method: str

class TerminalValueRequest(BaseModel):
    last_year_metric: float = Field(..., description="Última métrica proyectada (EBITDA o Ingresos)")
    multiple: float = Field(..., ge=0, description="Múltiplo de la industria")
    discount_rate: float = Field(..., ge=0, description="Costo de capital o WACC")
    years: int = Field(..., gt=0, description="Años para el exit")

class TerminalValueResponse(BaseModel):
    last_metric: float
    multiple: float
    terminal_value: float
    discounted_tv: float
    discount_rate: float
    years: int

# --- Working Capital ---

class CashCycleRequest(BaseModel):
    annual_revenue: float = Field(..., gt=0)
    accounts_receivable: float = Field(..., ge=0)
    annual_cogs: float = Field(..., gt=0)
    inventory: float = Field(..., ge=0)
    accounts_payable: float = Field(..., ge=0)
    days_in_year: int = Field(365, gt=0)

class CashCycleResponse(BaseModel):
    dso: float
    dio: float
    dpo: float
    ccc_days: float
    interpretation: str
    daily_sales: float
    capital_tied_up: float

# --- Bootstrapping / Cash Management ---

class RunwayRequest(BaseModel):
    initial_cash: float = Field(..., ge=0)
    monthly_revenue: float = Field(..., ge=0)
    monthly_fixed_costs: float = Field(..., ge=0)
    monthly_variable_costs: float = Field(0.0, ge=0)
    revenue_growth_rate: float = Field(0.0)

class RunwayResponse(BaseModel):
    initial_cash: float
    monthly_revenue: float
    monthly_burn: float
    net_burn: float
    runway_months: float
    death_valley_date_months: float
    survival_assessment: str
