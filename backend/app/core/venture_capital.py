"""
venture_capital.py — Matemáticas para Startups, VC y M&A.

Implementa lógicas específicas de financiamiento de riesgo:
- Notas convertibles (SAFE / Convertible Notes).
- Dilución de fundadores.
- Valor terminal (Terminal Value) y múltiplos de salida.
"""

from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ConvertibleNoteResult:
    """Resultado de la conversión de una nota convertible."""
    investment: float
    cap: float
    discount: float
    next_round_valuation: float
    
    effective_valuation: float
    investor_ownership_pct: float
    founder_retained_pct: float
    conversion_method: str  # "CAP", "DISCOUNT", or "NO_DISCOUNT"

@dataclass(frozen=True, slots=True)
class TerminalValueResult:
    """Resultado del cálculo de valor terminal."""
    last_metric: float
    multiple: float
    terminal_value: float
    discounted_tv: float
    discount_rate: float
    years: int

def convertible_note_conversion(
    investment: float,
    valuation_cap: float,
    discount_rate: float,
    next_round_pre_money: float,
) -> ConvertibleNoteResult:
    """
    Calcula la dilución de un fundador al convertir una nota convertible.
    Se utiliza el que más beneficie al inversor (menor valoración efectiva).
    
    Args:
        investment: El monto invertido en la nota.
        valuation_cap: El tope máximo de valoración (Cap).
        discount_rate: Descuento aplicable (ej. 0.20 para 20%).
        next_round_pre_money: Valoración pre-money en la nueva ronda.
        
    Returns:
        ConvertibleNoteResult con los porcentajes de propiedad y el método usado.
    """
    if investment <= 0:
        raise ValueError("La inversión debe ser mayor a 0.")
    if not (0 <= discount_rate < 1):
        raise ValueError("El descuento debe estar entre 0 y 1 (exclusivo).")
        
    discounted_val = next_round_pre_money * (1 - discount_rate)
    
    # El inversor obtiene la valoración MÁS BAJA (mejor precio por acción)
    if valuation_cap > 0 and valuation_cap < discounted_val:
        effective_val = valuation_cap
        method = "CAP"
    elif discount_rate > 0:
        effective_val = discounted_val
        method = "DISCOUNT"
    else:
        effective_val = next_round_pre_money
        method = "NO_DISCOUNT"
        
    # Asumiendo conversión en el momento previo a que el VC nuevo entre (Post-Money de la nota = Effective Val + Investment)
    post_money_val = effective_val + investment
    investor_pct = investment / post_money_val
    founder_pct = 1.0 - investor_pct
    
    return ConvertibleNoteResult(
        investment=investment,
        cap=valuation_cap,
        discount=discount_rate,
        next_round_valuation=next_round_pre_money,
        effective_valuation=round(effective_val, 2),
        investor_ownership_pct=round(investor_pct, 4),
        founder_retained_pct=round(founder_pct, 4),
        conversion_method=method
    )

def terminal_value_multiple(
    last_year_metric: float,
    multiple: float,
    discount_rate: float,
    years: int
) -> TerminalValueResult:
    """
    Calcula el Valor Terminal usando el método de Múltiplos
    (ej. 5x EBITDA, 10x Ingresos).
    
    Args:
        last_year_metric: Métrica del último año proyectado (EBITDA, Ingresos).
        multiple: Múltiplo de salida esperado en la industria.
        discount_rate: Tasa de descuento (WACC / Costo de Capital de VC).
        years: Año en el que ocurre la salida.
        
    Returns:
        TerminalValueResult con el valor futuro y presente descontado.
    """
    if multiple < 0:
        raise ValueError("El múltiplo no puede ser negativo.")
        
    tv = last_year_metric * multiple
    discounted = tv / ((1 + discount_rate) ** years)
    
    return TerminalValueResult(
        last_metric=round(last_year_metric, 2),
        multiple=multiple,
        terminal_value=round(tv, 2),
        discounted_tv=round(discounted, 2),
        discount_rate=discount_rate,
        years=years
    )
