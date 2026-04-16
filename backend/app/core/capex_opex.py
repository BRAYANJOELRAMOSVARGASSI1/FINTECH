"""
capex_opex.py — Análisis Comparativo CAPEX vs OPEX.

Este módulo implementa el análisis más completo del sistema:
la comparación entre adquirir un activo (CAPEX) vs. contratar
un servicio operativo recurrente (OPEX).

CAPEX (Capital Expenditure):
    - Inversión inicial grande (año 0, flujo NEGATIVO).
    - Depreciación anual → Escudo Fiscal.
    - Costo de mantenimiento anual.
    - Valor de salvamento al final de la vida útil.
    - Balance Sheet impact: el activo aparece como propiedad.

OPEX (Operational Expenditure):
    - Sin inversión inicial.
    - Pagos recurrentes (licencias, leasing, SaaS).
    - Escudo fiscal INMEDIATO (100% deducible).
    - Afectado por inflación.
    - Income Statement impact: gasto del período.

DECISIÓN:
    El sistema proyecta el Flujo de Caja Libre (FCF) de ambas opciones
    y las compara usando:
    1. VPN (descontado a WACC) → Menor costo = mejor.
    2. TIR (si el análisis es de inversión productiva).
    3. Análisis de sensibilidad (variando inflación y costos +/- 20%).

References:
    - Damodaran — Investment Valuation, Cap. 9 (CAPEX decisions)
    - NIC 17 / NIIF 16 — Arrendamientos
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.rates import _validate_rate
from app.core.taxes import (
    DepreciationMethod,
    after_tax_cost,
    asset_disposal,
    declining_balance_depreciation,
    straight_line_depreciation,
    sum_of_years_digits_depreciation,
    tax_shield,
)
from app.core.valuation import net_present_value


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CapexInput:
    """Entrada para análisis CAPEX."""

    initial_investment: float  # Inversión inicial (positivo)
    useful_life_years: int  # Vida útil del activo
    salvage_value: float  # Valor de salvamento al final
    annual_maintenance: float  # Costo de mantenimiento anual
    tax_rate: float  # Tasa impositiva (decimal)
    depreciation_method: DepreciationMethod = DepreciationMethod.STRAIGHT_LINE
    maintenance_growth_rate: float = 0.0  # Crecimiento anual del mantenimiento


@dataclass(frozen=True, slots=True)
class OpexInput:
    """Entrada para análisis OPEX."""

    annual_cost: float  # Costo anual del servicio/leasing
    contract_years: int  # Duración del contrato
    tax_rate: float  # Tasa impositiva (decimal)
    inflation_rate: float = 0.0  # Inflación anual esperada
    setup_cost: float = 0.0  # Costo inicial de configuración


@dataclass(frozen=True, slots=True)
class CapexAnalysis:
    """Resultado del análisis CAPEX."""

    cash_flows: list[float]
    depreciation_schedule: list[float]
    tax_shields: list[float]
    maintenance_costs: list[float]
    salvage_net_proceeds: float
    total_cost_nominal: float
    npv_cost: float  # VPN del costo total (negativo = gasto)
    year_labels: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class OpexAnalysis:
    """Resultado del análisis OPEX."""

    cash_flows: list[float]
    annual_costs_nominal: list[float]
    tax_savings: list[float]
    total_cost_nominal: float
    npv_cost: float
    year_labels: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SensitivityPoint:
    """Un punto del análisis de sensibilidad."""

    variable_name: str
    variation_pct: float
    capex_npv: float
    opex_npv: float
    recommendation: str


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Resultado completo de la comparación CAPEX vs OPEX."""

    capex: CapexAnalysis
    opex: OpexAnalysis
    npv_advantage: float  # Diferencia de VPN (positivo = CAPEX más barato)
    recommendation: str  # "CAPEX", "OPEX", "INDIFFERENT"
    explanation: str  # Explicación textual
    wacc_used: float
    sensitivity: list[SensitivityPoint] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------


def _validate_capex_input(inp: CapexInput) -> None:
    """Valida parámetros de entrada CAPEX."""
    if inp.initial_investment <= 0:
        raise ValueError("initial_investment debe ser > 0")
    if inp.useful_life_years < 1:
        raise ValueError("useful_life_years debe ser >= 1")
    if inp.salvage_value < 0:
        raise ValueError("salvage_value debe ser >= 0")
    if inp.salvage_value >= inp.initial_investment:
        raise ValueError("salvage_value debe ser < initial_investment")
    if not (0 <= inp.tax_rate < 1):
        raise ValueError(f"tax_rate debe estar en [0, 1), recibido: {inp.tax_rate}")
    if inp.annual_maintenance < 0:
        raise ValueError("annual_maintenance debe ser >= 0")


def _validate_opex_input(inp: OpexInput) -> None:
    """Valida parámetros de entrada OPEX."""
    if inp.annual_cost <= 0:
        raise ValueError("annual_cost debe ser > 0")
    if inp.contract_years < 1:
        raise ValueError("contract_years debe ser >= 1")
    if not (0 <= inp.tax_rate < 1):
        raise ValueError(f"tax_rate debe estar en [0, 1), recibido: {inp.tax_rate}")
    if inp.setup_cost < 0:
        raise ValueError("setup_cost debe ser >= 0")


# ---------------------------------------------------------------------------
# Análisis CAPEX
# ---------------------------------------------------------------------------


def analyze_capex(capex: CapexInput, wacc: float) -> CapexAnalysis:
    """Analiza la opción CAPEX (compra del activo).

    Proyección año a año:
    1. Año 0: -Inversión Inicial
    2. Años 1..n: -(Mantenimiento after-tax) + Escudo Fiscal por Depreciación
    3. Año n: + Valor de Salvamento neto (después de impuestos)

    El flujo relevante es el COSTO NETO después de considerar
    el beneficio fiscal de la depreciación.

    Args:
        capex: Parámetros del activo.
        wacc: Tasa de descuento (WACC de la empresa).

    Returns:
        CapexAnalysis con flujos proyectados y VPN del costo.
    """
    _validate_capex_input(capex)
    _validate_rate(wacc, "wacc")

    n = capex.useful_life_years

    # 1. Calcular depreciación según método
    if capex.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
        dep_schedule = straight_line_depreciation(
            capex.initial_investment, capex.salvage_value, n, capex.tax_rate
        )
    elif capex.depreciation_method == DepreciationMethod.DECLINING_BALANCE:
        dep_schedule = declining_balance_depreciation(
            capex.initial_investment, capex.salvage_value, n, capex.tax_rate
        )
    else:
        dep_schedule = sum_of_years_digits_depreciation(
            capex.initial_investment, capex.salvage_value, n, capex.tax_rate
        )

    depreciation = dep_schedule.annual_depreciation
    shields = dep_schedule.annual_tax_shield

    # 2. Costos de mantenimiento proyectados con crecimiento
    maintenance_costs = []
    for year in range(n):
        maint = capex.annual_maintenance * (1 + capex.maintenance_growth_rate) ** year
        maintenance_costs.append(round(maint, 2))

    # 3. Valor de salvamento neto de impuestos
    disposal = asset_disposal(
        original_cost=capex.initial_investment,
        accumulated_depreciation=dep_schedule.total_depreciation,
        sale_price=capex.salvage_value,
        tax_rate=capex.tax_rate,
    )

    # 4. Construir flujos de caja
    cash_flows = [-capex.initial_investment]  # Año 0

    for year in range(n):
        # Costo de mantenimiento después de impuestos (es deducible)
        maint_after_tax = after_tax_cost(maintenance_costs[year], capex.tax_rate)
        # Escudo fiscal de depreciación (ahorro)
        shield_benefit = shields[year]
        # Flujo neto del año
        cf = -maint_after_tax + shield_benefit
        cash_flows.append(round(cf, 2))

    # Agregar valor de salvamento neto al último año
    cash_flows[-1] = round(cash_flows[-1] + disposal.net_proceeds, 2)

    # 5. VPN del costo total
    npv_result = net_present_value(cash_flows, wacc)

    # Labels
    year_labels = [f"Año {i}" for i in range(n + 1)]

    return CapexAnalysis(
        cash_flows=cash_flows,
        depreciation_schedule=depreciation,
        tax_shields=shields,
        maintenance_costs=maintenance_costs,
        salvage_net_proceeds=disposal.net_proceeds,
        total_cost_nominal=round(
            capex.initial_investment
            + sum(maintenance_costs)
            - capex.salvage_value,
            2,
        ),
        npv_cost=npv_result.npv,
        year_labels=year_labels,
    )


# ---------------------------------------------------------------------------
# Análisis OPEX
# ---------------------------------------------------------------------------


def analyze_opex(opex: OpexInput, wacc: float) -> OpexAnalysis:
    """Analiza la opción OPEX (gasto operativo recurrente).

    Proyección año a año:
    1. Año 0: -Setup cost (si hay)
    2. Años 1..n: -(Costo anual ajustado por inflación) × (1 - Tax Rate)
       El OPEX es 100% deducible → escudo fiscal INMEDIATO.

    Args:
        opex: Parámetros del gasto operativo.
        wacc: Tasa de descuento (WACC).

    Returns:
        OpexAnalysis con flujos proyectados y VPN del costo.
    """
    _validate_opex_input(opex)
    _validate_rate(wacc, "wacc")

    n = opex.contract_years

    # Año 0: setup cost (si existe)
    setup_after_tax = after_tax_cost(opex.setup_cost, opex.tax_rate) if opex.setup_cost > 0 else 0.0
    cash_flows = [-setup_after_tax]

    annual_costs_nominal = []
    tax_savings_list = []

    for year in range(n):
        # Costo nominal con inflación
        nominal_cost = opex.annual_cost * (1 + opex.inflation_rate) ** year
        annual_costs_nominal.append(round(nominal_cost, 2))

        # Costo después de impuestos (el OPEX es 100% deducible)
        cost_after_tax = after_tax_cost(nominal_cost, opex.tax_rate)
        tax_saving = round(nominal_cost * opex.tax_rate, 2)
        tax_savings_list.append(tax_saving)

        cash_flows.append(round(-cost_after_tax, 2))

    # VPN del costo total
    npv_result = net_present_value(cash_flows, wacc)

    year_labels = [f"Año {i}" for i in range(n + 1)]

    return OpexAnalysis(
        cash_flows=cash_flows,
        annual_costs_nominal=annual_costs_nominal,
        tax_savings=tax_savings_list,
        total_cost_nominal=round(opex.setup_cost + sum(annual_costs_nominal), 2),
        npv_cost=npv_result.npv,
        year_labels=year_labels,
    )


# ---------------------------------------------------------------------------
# Comparación CAPEX vs OPEX
# ---------------------------------------------------------------------------


def compare_capex_vs_opex(
    capex: CapexInput,
    opex: OpexInput,
    wacc: float,
    run_sensitivity: bool = True,
) -> ComparisonResult:
    """Compara CAPEX vs OPEX y emite una recomendación.

    El sistema calcula el VPN del costo neto de cada opción.
    Como son COSTOS, el VPN será negativo (o menos negativo).
    La opción con VPN más ALTO (menos negativo) es la mejor.

    También ejecuta análisis de sensibilidad variando:
    - Inflación: ±20%, ±40%, ±60%
    - Costos de mantenimiento: ±20%, ±40%

    Args:
        capex: Parámetros CAPEX.
        opex: Parámetros OPEX.
        wacc: WACC de la empresa.
        run_sensitivity: Si True, ejecuta análisis de sensibilidad.

    Returns:
        ComparisonResult con ambos análisis, recomendación y sensibilidad.
    """
    _validate_rate(wacc, "wacc")

    # Igualar horizontes temporales
    # Si CAPEX tiene vida útil diferente al contrato OPEX, usar el mayor
    capex_analysis = analyze_capex(capex, wacc)
    opex_analysis = analyze_opex(opex, wacc)

    # VPN positivo = "menos costoso" en este contexto
    npv_advantage = capex_analysis.npv_cost - opex_analysis.npv_cost

    # Determinar recomendación
    tolerance = abs(max(capex_analysis.npv_cost, opex_analysis.npv_cost, key=abs)) * 0.01
    if abs(npv_advantage) < max(tolerance, 100):
        recommendation = "INDIFFERENT"
        explanation = (
            f"Ambas opciones tienen un costo similar en valor presente. "
            f"CAPEX VPN: ${capex_analysis.npv_cost:,.2f} vs OPEX VPN: ${opex_analysis.npv_cost:,.2f}. "
            f"La diferencia de ${abs(npv_advantage):,.2f} es insignificante. "
            f"Considere factores cualitativos como flexibilidad y riesgo operativo."
        )
    elif npv_advantage > 0:
        # CAPEX es menos negativo → más barato
        recommendation = "CAPEX"
        explanation = (
            f"CAPEX es más económico por ${abs(npv_advantage):,.2f} en valor presente. "
            f"CAPEX VPN: ${capex_analysis.npv_cost:,.2f} vs OPEX VPN: ${opex_analysis.npv_cost:,.2f}. "
            f"El escudo fiscal por depreciación (${sum(capex_analysis.tax_shields):,.2f} total) "
            f"y el valor de salvamento (${capex_analysis.salvage_net_proceeds:,.2f} neto) "
            f"hacen que la compra del activo sea la opción financieramente superior."
        )
    else:
        recommendation = "OPEX"
        explanation = (
            f"OPEX es más económico por ${abs(npv_advantage):,.2f} en valor presente. "
            f"CAPEX VPN: ${capex_analysis.npv_cost:,.2f} vs OPEX VPN: ${opex_analysis.npv_cost:,.2f}. "
            f"El gasto operativo, a pesar del efecto inflacionario, resulta más barato "
            f"que la inversión de capital considerando el costo de oportunidad (WACC={wacc*100:.2f}%)."
        )

    # --- Análisis de Sensibilidad ---
    sensitivity_points = []
    if run_sensitivity:
        # Variar inflación OPEX
        for variation in [-0.6, -0.4, -0.2, 0.2, 0.4, 0.6]:
            adjusted_inflation = opex.inflation_rate * (1 + variation)
            adjusted_opex = OpexInput(
                annual_cost=opex.annual_cost,
                contract_years=opex.contract_years,
                tax_rate=opex.tax_rate,
                inflation_rate=max(adjusted_inflation, -0.5),  # Piso de deflación
                setup_cost=opex.setup_cost,
            )
            opex_adj = analyze_opex(adjusted_opex, wacc)
            adv = capex_analysis.npv_cost - opex_adj.npv_cost
            rec = "CAPEX" if adv > 0 else "OPEX"

            sensitivity_points.append(
                SensitivityPoint(
                    variable_name="inflation_rate",
                    variation_pct=variation * 100,
                    capex_npv=capex_analysis.npv_cost,
                    opex_npv=opex_adj.npv_cost,
                    recommendation=rec,
                )
            )

        # Variar costo de mantenimiento CAPEX
        for variation in [-0.4, -0.2, 0.2, 0.4]:
            adjusted_maint = capex.annual_maintenance * (1 + variation)
            adjusted_capex = CapexInput(
                initial_investment=capex.initial_investment,
                useful_life_years=capex.useful_life_years,
                salvage_value=capex.salvage_value,
                annual_maintenance=adjusted_maint,
                tax_rate=capex.tax_rate,
                depreciation_method=capex.depreciation_method,
                maintenance_growth_rate=capex.maintenance_growth_rate,
            )
            capex_adj = analyze_capex(adjusted_capex, wacc)
            adv = capex_adj.npv_cost - opex_analysis.npv_cost
            rec = "CAPEX" if adv > 0 else "OPEX"

            sensitivity_points.append(
                SensitivityPoint(
                    variable_name="maintenance_cost",
                    variation_pct=variation * 100,
                    capex_npv=capex_adj.npv_cost,
                    opex_npv=opex_analysis.npv_cost,
                    recommendation=rec,
                )
            )

    return ComparisonResult(
        capex=capex_analysis,
        opex=opex_analysis,
        npv_advantage=round(npv_advantage, 2),
        recommendation=recommendation,
        explanation=explanation,
        wacc_used=wacc,
        sensitivity=sensitivity_points,
    )
