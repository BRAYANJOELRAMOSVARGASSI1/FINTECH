"""
api/v1/startup_routes.py — Rutas para módulos de Capital de Trabajo y Startups.
"""

from fastapi import APIRouter
from app.schemas.startup import (
    ConvertibleNoteRequest, ConvertibleNoteResponse,
    TerminalValueRequest, TerminalValueResponse,
    CashCycleRequest, CashCycleResponse,
    RunwayRequest, RunwayResponse
)
from app.core import venture_capital, working_capital, cash_management

router = APIRouter(prefix="/startup", tags=["Startups & Pymes"])

@router.post("/convertible-note", response_model=ConvertibleNoteResponse)
def analyze_convertible_note(req: ConvertibleNoteRequest):
    """Evalúa la conversión de una nota y dilución de founders."""
    result = venture_capital.convertible_note_conversion(
        investment=req.investment,
        valuation_cap=req.valuation_cap,
        discount_rate=req.discount_rate,
        next_round_pre_money=req.next_round_pre_money
    )
    return ConvertibleNoteResponse(
        investment=result.investment,
        cap=result.cap,
        discount=result.discount,
        next_round_valuation=result.next_round_valuation,
        effective_valuation=result.effective_valuation,
        investor_ownership_pct=result.investor_ownership_pct,
        founder_retained_pct=result.founder_retained_pct,
        conversion_method=result.conversion_method
    )

@router.post("/terminal-value", response_model=TerminalValueResponse)
def compute_terminal_value(req: TerminalValueRequest):
    """Calcula el valor residual de un negocio por método de múltiplos."""
    result = venture_capital.terminal_value_multiple(
        last_year_metric=req.last_year_metric,
        multiple=req.multiple,
        discount_rate=req.discount_rate,
        years=req.years
    )
    return TerminalValueResponse(
        last_metric=result.last_metric,
        multiple=result.multiple,
        terminal_value=result.terminal_value,
        discounted_tv=result.discounted_tv,
        discount_rate=result.discount_rate,
        years=result.years
    )

@router.post("/working-capital/ccc", response_model=CashCycleResponse)
def compute_cash_cycle(req: CashCycleRequest):
    """Calcula el Ciclo de Conversión de Efectivo para diagnosticar inmovilizados."""
    result = working_capital.cash_conversion_cycle(
        annual_revenue=req.annual_revenue,
        accounts_receivable=req.accounts_receivable,
        annual_cogs=req.annual_cogs,
        inventory=req.inventory,
        accounts_payable=req.accounts_payable,
        days_in_year=req.days_in_year
    )
    return CashCycleResponse(
        dso=result.dso,
        dio=result.dio,
        dpo=result.dpo,
        ccc_days=result.ccc_days,
        interpretation=result.interpretation,
        daily_sales=result.daily_sales,
        capital_tied_up=result.capital_tied_up
    )

@router.post("/runway", response_model=RunwayResponse)
def compute_startup_runway(req: RunwayRequest):
    """Calcula el espacio de supervivencia y puntos de equilibrio en caja."""
    result = cash_management.calculate_startup_runway(
        initial_cash=req.initial_cash,
        monthly_revenue=req.monthly_revenue,
        monthly_fixed_costs=req.monthly_fixed_costs,
        monthly_variable_costs=req.monthly_variable_costs,
        revenue_growth_rate=req.revenue_growth_rate
    )
    
    # Manejar el infinito JSON reemplazándolo por un valor de flag en el response JSON 
    # O Pydantic lo mandara como Inf si allow_inf_nan es true. FastAPI soporta Infinity en JSON.
    return RunwayResponse(
        initial_cash=result.initial_cash,
        monthly_revenue=result.monthly_revenue,
        monthly_burn=result.monthly_burn,
        net_burn=result.net_burn,
        runway_months=result.runway_months,
        death_valley_date_months=result.death_valley_date_months,
        survival_assessment=result.survival_assessment
    )
