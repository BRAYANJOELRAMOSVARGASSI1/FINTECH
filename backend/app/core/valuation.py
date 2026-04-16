"""
valuation.py — Valoración Financiera: VPN, TIR, FCF, Payback.

Este módulo implementa las métricas fundamentales para evaluar
la viabilidad de un proyecto de inversión. Es el segundo pilar
del motor financiero después de rates.py.

REGLA DE DECISIÓN:
    - VPN > 0  → El proyecto CREA valor → ACEPTAR
    - VPN = 0  → El proyecto es indiferente
    - VPN < 0  → El proyecto DESTRUYE valor → RECHAZAR
    - TIR > WACC → ACEPTAR
    - TIR < WACC → RECHAZAR

Referencias:
    - Damodaran — Investment Valuation
    - Ross, Westerfield & Jordan — Corporate Finance
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import numpy_financial as npf


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NPVResult:
    """Resultado del cálculo de Valor Presente Neto."""

    npv: float
    discount_rate: float
    periods: int
    decision: str  # "ACCEPT", "REJECT", "INDIFFERENT"
    present_values: list[float] = field(default_factory=list)

    @property
    def npv_formatted(self) -> str:
        """VPN formateado como moneda."""
        sign = "+" if self.npv >= 0 else ""
        return f"{sign}{self.npv:,.2f}"


@dataclass(frozen=True, slots=True)
class IRRResult:
    """Resultado del cálculo de Tasa Interna de Retorno."""

    irr: float | None
    converged: bool
    hurdle_rate: float | None = None
    decision: str | None = None  # "ACCEPT", "REJECT" si se provee hurdle

    @property
    def irr_percentage(self) -> float | None:
        """TIR como porcentaje."""
        return round(self.irr * 100, 4) if self.irr is not None else None


@dataclass(frozen=True, slots=True)
class PaybackResult:
    """Resultado del período de recuperación."""

    simple_payback: float | None
    discounted_payback: float | None
    discount_rate: float
    cumulative_flows: list[float] = field(default_factory=list)
    cumulative_pv_flows: list[float] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ProfitabilityIndexResult:
    """Resultado del índice de rentabilidad."""

    pi: float
    decision: str  # PI > 1 = ACCEPT


@dataclass(frozen=True, slots=True)
class ValuationSummary:
    """Resumen completo de valoración de un proyecto."""

    npv: NPVResult
    irr: IRRResult
    payback: PaybackResult
    profitability_index: ProfitabilityIndexResult
    cash_flows: list[float]
    discount_rate: float


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------


def _validate_cash_flows(cash_flows: list[float], min_periods: int = 2) -> None:
    """Valida el vector de flujos de caja.

    Args:
        cash_flows: Lista de flujos. Índice 0 = inversión inicial.
        min_periods: Mínimo de períodos requeridos.

    Raises:
        ValueError: Si los flujos no cumplen requisitos.
    """
    if len(cash_flows) < min_periods:
        raise ValueError(
            f"Se requieren al menos {min_periods} períodos de flujo de caja, "
            f"recibidos: {len(cash_flows)}"
        )

    if not all(math.isfinite(cf) for cf in cash_flows):
        raise ValueError("Todos los flujos de caja deben ser números finitos.")


def _validate_discount_rate(rate: float) -> None:
    """Valida la tasa de descuento."""
    if not math.isfinite(rate):
        raise ValueError(f"La tasa de descuento debe ser finita, recibido: {rate}")
    if rate <= -1:
        raise ValueError("La tasa de descuento debe ser > -100%.")


# ---------------------------------------------------------------------------
# Funciones de Valoración
# ---------------------------------------------------------------------------


def net_present_value(
    cash_flows: list[float],
    discount_rate: float,
) -> NPVResult:
    """Calcula el Valor Presente Neto (VPN/NPV).

    VPN = Σ [CF_t / (1 + r)^t] para t = 0, 1, ..., n

    El VPN descuenta todos los flujos futuros al presente usando
    la tasa de descuento (típicamente WACC). Representa cuánto
    valor CREA o DESTRUYE el proyecto en términos de hoy.

    Args:
        cash_flows: Lista de flujos. Índice 0 = inversión inicial (generalmente negativo).
        discount_rate: Tasa de descuento por período (en decimal).

    Returns:
        NPVResult con el VPN, decisión y valores presentes individuales.

    Examples:
        >>> result = net_present_value([-100000, 30000, 40000, 50000, 30000], 0.10)
        >>> result.npv  # VPN > 0 → ACEPTAR
        16066.42...
    """
    _validate_cash_flows(cash_flows)
    _validate_discount_rate(discount_rate)

    npv_value = float(npf.npv(discount_rate, cash_flows))

    # Calcular valor presente de cada flujo individual
    present_values = [
        cf / (1 + discount_rate) ** t
        for t, cf in enumerate(cash_flows)
    ]

    # Regla de decisión
    if abs(npv_value) < 0.01:  # Tolerancia para "cero"
        decision = "INDIFFERENT"
    elif npv_value > 0:
        decision = "ACCEPT"
    else:
        decision = "REJECT"

    return NPVResult(
        npv=round(npv_value, 2),
        discount_rate=discount_rate,
        periods=len(cash_flows) - 1,
        decision=decision,
        present_values=[round(pv, 2) for pv in present_values],
    )


def internal_rate_of_return(
    cash_flows: list[float],
    hurdle_rate: float | None = None,
) -> IRRResult:
    """Calcula la Tasa Interna de Retorno (TIR/IRR).

    La TIR es la tasa de descuento que hace VPN = 0.
    Es el "rendimiento implícito" del proyecto.

    Args:
        cash_flows: Lista de flujos. Debe tener al menos un cambio de signo.
        hurdle_rate: Tasa mínima requerida (WACC) para emitir decisión.

    Returns:
        IRRResult con la TIR y decisión si se provee hurdle.

    Note:
        La TIR puede no converger si los flujos no cambian de signo
        o si hay múltiples TIRs. En ese caso, IRRResult.converged = False.
    """
    _validate_cash_flows(cash_flows)

    try:
        irr_value = float(npf.irr(cash_flows))
        if not math.isfinite(irr_value):
            return IRRResult(irr=None, converged=False, hurdle_rate=hurdle_rate)
    except (ValueError, RuntimeError):
        return IRRResult(irr=None, converged=False, hurdle_rate=hurdle_rate)

    decision = None
    if hurdle_rate is not None:
        decision = "ACCEPT" if irr_value > hurdle_rate else "REJECT"

    return IRRResult(
        irr=round(irr_value, 6),
        converged=True,
        hurdle_rate=hurdle_rate,
        decision=decision,
    )


def profitability_index(
    cash_flows: list[float],
    discount_rate: float,
) -> ProfitabilityIndexResult:
    """Calcula el Índice de Rentabilidad (PI / Benefit-Cost Ratio).

    PI = VP de flujos futuros positivos / |Inversión inicial|

    PI > 1 → El proyecto genera más valor del que cuesta → ACEPTAR.
    PI = 1 → Breakeven.
    PI < 1 → RECHAZAR.

    Útil para comparar proyectos cuando hay restricción de capital.

    Args:
        cash_flows: Lista de flujos. Índice 0 = inversión inicial.
        discount_rate: Tasa de descuento.

    Returns:
        ProfitabilityIndexResult con el PI y decisión.
    """
    _validate_cash_flows(cash_flows)
    _validate_discount_rate(discount_rate)

    initial_investment = abs(cash_flows[0])
    if initial_investment == 0:
        raise ValueError("La inversión inicial (cash_flows[0]) no puede ser cero para PI.")

    # VP de flujos futuros (desde período 1 en adelante)
    pv_future = sum(
        cf / (1 + discount_rate) ** t
        for t, cf in enumerate(cash_flows[1:], start=1)
    )

    pi_value = pv_future / initial_investment

    if abs(pi_value - 1) < 0.001:
        decision = "INDIFFERENT"
    elif pi_value > 1:
        decision = "ACCEPT"
    else:
        decision = "REJECT"

    return ProfitabilityIndexResult(pi=round(pi_value, 4), decision=decision)


def payback_period(
    cash_flows: list[float],
    discount_rate: float,
) -> PaybackResult:
    """Calcula el período de recuperación simple y descontado.

    - Simple: ¿Cuándo recupero mi inversión en términos nominales?
    - Descontado: ¿Cuándo recupero en términos de valor presente?

    El payback descontado es siempre >= al simple porque
    descuenta los flujos futuros.

    Args:
        cash_flows: Lista de flujos.
        discount_rate: Tasa de descuento para payback descontado.

    Returns:
        PaybackResult con ambos períodos de recuperación.
    """
    _validate_cash_flows(cash_flows)
    _validate_discount_rate(discount_rate)

    # --- Payback Simple ---
    cumulative = []
    running_sum = 0.0
    for cf in cash_flows:
        running_sum += cf
        cumulative.append(round(running_sum, 2))

    simple_payback = _find_crossover(cumulative)

    # --- Payback Descontado ---
    pv_flows = [cf / (1 + discount_rate) ** t for t, cf in enumerate(cash_flows)]
    cumulative_pv = []
    running_pv = 0.0
    for pv in pv_flows:
        running_pv += pv
        cumulative_pv.append(round(running_pv, 2))

    discounted_payback = _find_crossover(cumulative_pv)

    return PaybackResult(
        simple_payback=simple_payback,
        discounted_payback=discounted_payback,
        discount_rate=discount_rate,
        cumulative_flows=cumulative,
        cumulative_pv_flows=cumulative_pv,
    )


def _find_crossover(cumulative: list[float]) -> float | None:
    """Encuentra el punto exacto donde el acumulado cruza de negativo a positivo.

    Interpola linealmente para obtener el período fraccionario exacto.

    Returns:
        Período de recuperación con interpolación, o None si nunca se recupera.
    """
    for i in range(1, len(cumulative)):
        if cumulative[i] >= 0 and cumulative[i - 1] < 0:
            # Interpolación lineal entre período i-1 e i
            fraction = -cumulative[i - 1] / (cumulative[i] - cumulative[i - 1])
            return round((i - 1) + fraction, 2)
    # Si empieza positivo, payback = 0
    if cumulative and cumulative[0] >= 0:
        return 0.0
    return None


def free_cash_flow(
    revenue: list[float],
    operating_expenses: list[float],
    capex: list[float],
    tax_rate: float,
    depreciation: list[float],
    working_capital_changes: list[float] | None = None,
) -> list[float]:
    """Calcula el Flujo de Caja Libre (FCF) período a período.

    FCF = (Revenue - OpEx - Depreciation) * (1 - Tax) + Depreciation - CapEx - ΔWC

    Equivalentemente:
    FCF = EBIT * (1 - T) + Depreciation - CapEx - ΔWC
    FCF = NOPAT + Depreciation - CapEx - ΔWC

    La depreciación se SUMA de vuelta porque es un gasto contable
    y no un flujo de efectivo real, pero SÍ genera escudo fiscal.

    Args:
        revenue: Ingresos por período.
        operating_expenses: Gastos operativos por período (sin deprec).
        capex: Inversiones de capital por período (positivos = gasto).
        tax_rate: Tasa impositiva corporativa (decimal).
        depreciation: Depreciación contable por período.
        working_capital_changes: Cambios en capital de trabajo. None = ignorar.

    Returns:
        Lista con FCF por período.

    Raises:
        ValueError: Si las listas tienen longitudes inconsistentes.
    """
    n = len(revenue)
    if not all(len(lst) == n for lst in [operating_expenses, capex, depreciation]):
        raise ValueError("Todas las listas deben tener la misma longitud.")

    if not (0 <= tax_rate < 1):
        raise ValueError(f"tax_rate debe estar en [0, 1), recibido: {tax_rate}")

    if working_capital_changes is None:
        working_capital_changes = [0.0] * n
    elif len(working_capital_changes) != n:
        raise ValueError("working_capital_changes debe tener la misma longitud que revenue.")

    fcf = []
    for t in range(n):
        ebit = revenue[t] - operating_expenses[t] - depreciation[t]
        nopat = ebit * (1 - tax_rate)
        fcf_t = nopat + depreciation[t] - capex[t] - working_capital_changes[t]
        fcf.append(round(fcf_t, 2))

    return fcf


def full_valuation(
    cash_flows: list[float],
    discount_rate: float,
    hurdle_rate: float | None = None,
) -> ValuationSummary:
    """Ejecuta la valoración completa de un proyecto.

    Calcula VPN, TIR, Payback y PI en una sola llamada.

    Args:
        cash_flows: Flujos de caja del proyecto.
        discount_rate: Tasa de descuento (WACC).
        hurdle_rate: Tasa mínima para decisión de TIR. Default = discount_rate.

    Returns:
        ValuationSummary con todas las métricas.
    """
    if hurdle_rate is None:
        hurdle_rate = discount_rate

    npv_result = net_present_value(cash_flows, discount_rate)
    irr_result = internal_rate_of_return(cash_flows, hurdle_rate)
    payback_result = payback_period(cash_flows, discount_rate)
    pi_result = profitability_index(cash_flows, discount_rate)

    return ValuationSummary(
        npv=npv_result,
        irr=irr_result,
        payback=payback_result,
        profitability_index=pi_result,
        cash_flows=cash_flows,
        discount_rate=discount_rate,
    )
