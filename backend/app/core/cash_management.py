"""
cash_management.py — Gestión de Tesorería y Bootstrapping.

Implementa:
- Net Burn Rate & Gross Burn Rate.
- Runway (Meses de vida).
- Breakeven (Punto de equilibrio en caja).
"""

from __future__ import annotations
from dataclasses import dataclass
import math

@dataclass(frozen=True, slots=True)
class RunwayResult:
    """Resultado del cálculo de Runway para Startups."""
    initial_cash: float
    monthly_revenue: float
    monthly_burn: float
    net_burn: float
    runway_months: float
    death_valley_date_months: float
    survival_assessment: str

def calculate_startup_runway(
    initial_cash: float,
    monthly_revenue: float,
    monthly_fixed_costs: float,
    monthly_variable_costs: float = 0.0,
    revenue_growth_rate: float = 0.0
) -> RunwayResult:
    """
    Calcula cuántos meses sobrevive la empresa con la caja actual.
    
    Args:
        initial_cash: Caja o liquidez inicial.
        monthly_revenue: Ingresos mensuales promedio.
        monthly_fixed_costs: Costos fijos (salarios, oficina, servidores).
        monthly_variable_costs: Costos que dependen de la venta.
        revenue_growth_rate: Tasa de crecimiento mensual de ingresos.
        
    Returns:
        RunwayResult con el análisis de supervivencia.
    """
    if initial_cash < 0:
        raise ValueError("La caja inicial no puede ser negativa.")
        
    gross_burn = monthly_fixed_costs + monthly_variable_costs
    net_burn = gross_burn - monthly_revenue
    
    # Si net_burn es negativo o cero, la empresa es rentable o breakeven
    if net_burn <= 0:
        return RunwayResult(
            initial_cash=initial_cash,
            monthly_revenue=monthly_revenue,
            monthly_burn=gross_burn,
            net_burn=net_burn,
            runway_months=float('inf'),
            death_valley_date_months=float('inf'),
            survival_assessment="Rentable (Default Alive). El Runway es infinito."
        )
        
    # Situación de pérdida mensual constante
    if revenue_growth_rate == 0.0:
        runway = initial_cash / net_burn
    else:
        # Si los ingresos crecen o decrecen, hay que iterar mes a mes
        cash = initial_cash
        rev = monthly_revenue
        months = 0
        while cash > 0 and months < 120:  # Cap at 10 years
            cash -= (gross_burn - rev)
            rev *= (1 + revenue_growth_rate)
            months += 1
            if (gross_burn - rev) <= 0:
                break # Alcanzó rentabilidad antes de morir
                
        if cash > 0:
            runway = float('inf')
        else:
            runway = months + (cash / (gross_burn - (rev / (1 + revenue_growth_rate)))) # Fracción de mes
            
    if runway < 6:
        assessment = "Crítico: Menos de 6 meses de vida. Reducir Burn o buscar capital INMEDIATO."
    elif runway < 12:
        assessment = "Precaución: Menos de 1 año. Preparar ronda o ajustar modelo."
    else:
        assessment = "Saludable: Más de 12 meses de vida. (Default Dead pero con tiempo)."

    return RunwayResult(
        initial_cash=initial_cash,
        monthly_revenue=round(monthly_revenue, 2),
        monthly_burn=round(gross_burn, 2),
        net_burn=round(net_burn if revenue_growth_rate == 0 else (gross_burn - monthly_revenue), 2),
        runway_months=round(runway, 1) if runway != float('inf') else float('inf'),
        death_valley_date_months=round(runway, 1) if runway != float('inf') else float('inf'),
        survival_assessment=assessment
    )
