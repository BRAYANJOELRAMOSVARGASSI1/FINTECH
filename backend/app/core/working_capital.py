"""
working_capital.py — Análisis de Capital de Trabajo.

Implementa:
- DSO (Days Sales Outstanding) - Días de cobro.
- DPO (Days Payable Outstanding) - Días de pago.
- DIO (Days Inventory Outstanding) - Días de inventario.
- CCC (Cash Conversion Cycle) - Ciclo de conversión de efectivo.
"""

from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class CashCycleResult:
    """Resultado del Ciclo de Conversión de Efectivo (CCC)."""
    dso: float
    dio: float
    dpo: float
    ccc_days: float
    interpretation: str
    daily_sales: float
    capital_tied_up: float

def cash_conversion_cycle(
    annual_revenue: float,
    accounts_receivable: float,
    annual_cogs: float,
    inventory: float,
    accounts_payable: float,
    days_in_year: int = 365
) -> CashCycleResult:
    """
    Calcula el Ciclo de Conversión de Efectivo (CCC) o Cash Cycle.
    
    Indicador de cuánto tiempo tarda una empresa en convertir sus
    inversiones en inventario y otros recursos en flujos de efectivo.
    
    CCC = DIO + DSO - DPO
    """
    if annual_revenue <= 0 or annual_cogs <= 0:
        raise ValueError("Los ingresos anuales y el costo de ventas deben ser > 0.")
        
    dso = (accounts_receivable / annual_revenue) * days_in_year
    dio = (inventory / annual_cogs) * days_in_year
    dpo = (accounts_payable / annual_cogs) * days_in_year
    
    ccc = dio + dso - dpo
    
    if ccc < 0:
        interpretation = "Negativo (Excelente): Los proveedores financian la operación."
    elif ccc < 30:
        interpretation = "Bajo (Bueno): Dinero rápido y alta liquidez."
    else:
        interpretation = "Alto (Riesgoso): El efectivo se estanca, requiere financiamiento propio."
        
    daily_sales = annual_revenue / days_in_year
    capital_tied = ccc * (annual_cogs / days_in_year) if ccc > 0 else 0.0
    
    return CashCycleResult(
        dso=round(dso, 2),
        dio=round(dio, 2),
        dpo=round(dpo, 2),
        ccc_days=round(ccc, 2),
        interpretation=interpretation,
        daily_sales=round(daily_sales, 2),
        capital_tied_up=round(capital_tied, 2)
    )
