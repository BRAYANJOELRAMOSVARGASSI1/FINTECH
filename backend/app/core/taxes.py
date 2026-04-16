"""
taxes.py — Depreciación, Escudos Fiscales y Beneficios Tributarios.

Módulo especializado en el tratamiento fiscal de activos y gastos.
El escudo fiscal es uno de los conceptos más poderosos en finanzas
corporativas — convierte un gasto en un ahorro real de impuestos.

Conceptos clave:
    - Depreciación: Distribución contable del costo de un activo en su vida útil.
      NO es un flujo de efectivo, pero REDUCE la base imponible.
    - Escudo Fiscal: Ahorro = Depreciación × Tasa_Impositiva.
    - Valor en Libros: Costo original - Depreciación acumulada.
    - Ganancia/Pérdida en Venta: Si Precio de Venta > Valor en Libros → ganancia gravable.

Métodos de depreciación implementados:
    1. Línea Recta (Straight-Line): Uniforme cada año.
    2. Doble Saldo Decreciente (DDB): Acelerada, más depreciación al inicio.
    3. Suma de Dígitos de los Años (SYD): Acelerada, ponderada.
    4. Unidades de Producción: Basada en uso real.

Referencias:
    - NIC 16 (IAS 16) — Propiedades, Planta y Equipo
    - NIIF / IFRS para tratamiento contable
    - Código tributario: la tasa impositiva varía por jurisdicción
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Enums y Data Classes
# ---------------------------------------------------------------------------


class DepreciationMethod(str, Enum):
    """Métodos de depreciación soportados."""

    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"
    SUM_OF_YEARS_DIGITS = "sum_of_years_digits"
    UNITS_OF_PRODUCTION = "units_of_production"


@dataclass(frozen=True, slots=True)
class DepreciationScheduleRow:
    """Fila individual del schedule de depreciación."""

    year: int
    depreciation_expense: float
    accumulated_depreciation: float
    book_value: float
    tax_shield: float


@dataclass(frozen=True, slots=True)
class DepreciationSchedule:
    """Tabla completa de depreciación de un activo."""

    method: DepreciationMethod
    original_cost: float
    salvage_value: float
    useful_life: int
    rows: list[DepreciationScheduleRow] = field(default_factory=list)
    total_depreciation: float = 0.0
    total_tax_shield: float = 0.0
    annual_depreciation: list[float] = field(default_factory=list)
    annual_tax_shield: list[float] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class AssetDisposalResult:
    """Resultado de la venta/disposición de un activo."""

    sale_price: float
    book_value_at_sale: float
    gain_or_loss: float
    tax_on_gain: float
    net_proceeds: float  # sale_price - tax_on_gain (o + tax_benefit si pérdida)
    is_gain: bool


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------


def _validate_asset_params(cost: float, salvage: float, useful_life: int) -> None:
    """Valida los parámetros de un activo para depreciación."""
    if cost <= 0:
        raise ValueError(f"El costo del activo debe ser > 0, recibido: {cost}")
    if salvage < 0:
        raise ValueError(f"El valor de salvamento debe ser >= 0, recibido: {salvage}")
    if salvage >= cost:
        raise ValueError(
            f"El valor de salvamento ({salvage}) debe ser < costo ({cost}). "
            "Un activo no puede valer más al final de su vida útil."
        )
    if useful_life < 1:
        raise ValueError(f"La vida útil debe ser >= 1 año, recibido: {useful_life}")


def _validate_tax_rate(tax_rate: float) -> None:
    """Valida la tasa impositiva."""
    if not (0 <= tax_rate < 1):
        raise ValueError(f"tax_rate debe estar en [0, 1), recibido: {tax_rate}")


# ---------------------------------------------------------------------------
# Depreciación — Línea Recta
# ---------------------------------------------------------------------------


def straight_line_depreciation(
    cost: float,
    salvage: float,
    useful_life: int,
    tax_rate: float = 0.0,
) -> DepreciationSchedule:
    """Depreciación por el método de Línea Recta.

    Fórmula: D_anual = (Costo - Valor_Salvamento) / Vida_Útil

    Es el método más simple y conservador. La depreciación es
    CONSTANTE cada año.

    Args:
        cost: Costo original del activo.
        salvage: Valor de salvamento al final de la vida útil.
        useful_life: Vida útil en años.
        tax_rate: Tasa impositiva para calcular escudo fiscal.

    Returns:
        DepreciationSchedule con la tabla completa.

    Examples:
        >>> result = straight_line_depreciation(100000, 10000, 5, 0.30)
        >>> result.annual_depreciation  # [18000, 18000, 18000, 18000, 18000]
        >>> result.annual_tax_shield    # [5400, 5400, 5400, 5400, 5400]
    """
    _validate_asset_params(cost, salvage, useful_life)
    _validate_tax_rate(tax_rate)

    depreciable_base = cost - salvage
    annual_dep = depreciable_base / useful_life

    rows = []
    accumulated = 0.0
    annual_deps = []
    annual_shields = []

    for year in range(1, useful_life + 1):
        accumulated += annual_dep
        book_value = cost - accumulated
        shield = annual_dep * tax_rate

        rows.append(
            DepreciationScheduleRow(
                year=year,
                depreciation_expense=round(annual_dep, 2),
                accumulated_depreciation=round(accumulated, 2),
                book_value=round(book_value, 2),
                tax_shield=round(shield, 2),
            )
        )
        annual_deps.append(round(annual_dep, 2))
        annual_shields.append(round(shield, 2))

    return DepreciationSchedule(
        method=DepreciationMethod.STRAIGHT_LINE,
        original_cost=cost,
        salvage_value=salvage,
        useful_life=useful_life,
        rows=rows,
        total_depreciation=round(depreciable_base, 2),
        total_tax_shield=round(depreciable_base * tax_rate, 2),
        annual_depreciation=annual_deps,
        annual_tax_shield=annual_shields,
    )


# ---------------------------------------------------------------------------
# Depreciación — Doble Saldo Decreciente (DDB)
# ---------------------------------------------------------------------------


def declining_balance_depreciation(
    cost: float,
    salvage: float,
    useful_life: int,
    tax_rate: float = 0.0,
    factor: float = 2.0,
) -> DepreciationSchedule:
    """Depreciación acelerada por Doble Saldo Decreciente (DDB).

    Fórmula: D_t = factor/vida_útil × Valor_en_Libros_(t-1)

    Genera mayor depreciación en los primeros años → mayor
    escudo fiscal temprano → mayor VPN del ahorro fiscal.

    El valor en libros NUNCA cae por debajo del valor de salvamento.

    Args:
        cost: Costo original del activo.
        salvage: Valor de salvamento.
        useful_life: Vida útil en años.
        tax_rate: Tasa impositiva.
        factor: Multiplicador (2.0 = doble, 1.5 = 150%).

    Returns:
        DepreciationSchedule con la tabla completa.
    """
    _validate_asset_params(cost, salvage, useful_life)
    _validate_tax_rate(tax_rate)
    if factor <= 0:
        raise ValueError(f"El factor DDB debe ser > 0, recibido: {factor}")

    rate = factor / useful_life
    book_value = cost
    accumulated = 0.0
    rows = []
    annual_deps = []
    annual_shields = []

    for year in range(1, useful_life + 1):
        dep = book_value * rate

        # No depreciar por debajo del valor de salvamento
        if book_value - dep < salvage:
            dep = max(book_value - salvage, 0)

        accumulated += dep
        book_value -= dep
        shield = dep * tax_rate

        rows.append(
            DepreciationScheduleRow(
                year=year,
                depreciation_expense=round(dep, 2),
                accumulated_depreciation=round(accumulated, 2),
                book_value=round(book_value, 2),
                tax_shield=round(shield, 2),
            )
        )
        annual_deps.append(round(dep, 2))
        annual_shields.append(round(shield, 2))

    total_dep = sum(annual_deps)
    total_shield = sum(annual_shields)

    return DepreciationSchedule(
        method=DepreciationMethod.DECLINING_BALANCE,
        original_cost=cost,
        salvage_value=salvage,
        useful_life=useful_life,
        rows=rows,
        total_depreciation=round(total_dep, 2),
        total_tax_shield=round(total_shield, 2),
        annual_depreciation=annual_deps,
        annual_tax_shield=annual_shields,
    )


# ---------------------------------------------------------------------------
# Depreciación — Suma de Dígitos de los Años (SYD)
# ---------------------------------------------------------------------------


def sum_of_years_digits_depreciation(
    cost: float,
    salvage: float,
    useful_life: int,
    tax_rate: float = 0.0,
) -> DepreciationSchedule:
    """Depreciación acelerada por Suma de Dígitos de los Años.

    Fórmula: D_t = (vida_restante / SYD) × Base_Depreciable
    SYD = n(n+1)/2

    Método acelerado intermedio entre línea recta y DDB.

    Args:
        cost: Costo original.
        salvage: Valor de salvamento.
        useful_life: Vida útil en años.
        tax_rate: Tasa impositiva.

    Returns:
        DepreciationSchedule completa.
    """
    _validate_asset_params(cost, salvage, useful_life)
    _validate_tax_rate(tax_rate)

    depreciable_base = cost - salvage
    syd = useful_life * (useful_life + 1) / 2  # Suma de dígitos

    rows = []
    accumulated = 0.0
    annual_deps = []
    annual_shields = []

    for year in range(1, useful_life + 1):
        remaining_life = useful_life - year + 1
        dep = (remaining_life / syd) * depreciable_base
        accumulated += dep
        book_value = cost - accumulated
        shield = dep * tax_rate

        rows.append(
            DepreciationScheduleRow(
                year=year,
                depreciation_expense=round(dep, 2),
                accumulated_depreciation=round(accumulated, 2),
                book_value=round(max(book_value, salvage), 2),
                tax_shield=round(shield, 2),
            )
        )
        annual_deps.append(round(dep, 2))
        annual_shields.append(round(shield, 2))

    return DepreciationSchedule(
        method=DepreciationMethod.SUM_OF_YEARS_DIGITS,
        original_cost=cost,
        salvage_value=salvage,
        useful_life=useful_life,
        rows=rows,
        total_depreciation=round(depreciable_base, 2),
        total_tax_shield=round(depreciable_base * tax_rate, 2),
        annual_depreciation=annual_deps,
        annual_tax_shield=annual_shields,
    )


# ---------------------------------------------------------------------------
# Escudo Fiscal
# ---------------------------------------------------------------------------


def tax_shield(depreciation: list[float], tax_rate: float) -> list[float]:
    """Calcula el escudo fiscal por depreciación.

    Escudo = Depreciación × Tasa_Impositiva

    El escudo fiscal es un AHORRO REAL de efectivo. Si una empresa
    deprecia $100,000 y paga 30% de impuestos, ahorra $30,000
    en impuestos que NO tiene que pagar.

    Args:
        depreciation: Lista de depreciación por período.
        tax_rate: Tasa impositiva corporativa.

    Returns:
        Lista de escudos fiscales por período.
    """
    _validate_tax_rate(tax_rate)
    return [round(d * tax_rate, 2) for d in depreciation]


def after_tax_cost(before_tax_cost: float, tax_rate: float) -> float:
    """Calcula el costo después de impuestos de un gasto deducible.

    Costo_después = Costo_antes × (1 - Tasa_Impositiva)

    Si un gasto es deducible, su costo REAL es menor porque
    reduce la base imponible.

    Args:
        before_tax_cost: Costo antes de impuestos.
        tax_rate: Tasa impositiva.

    Returns:
        Costo real después del beneficio fiscal.

    Examples:
        >>> after_tax_cost(10000, 0.30)
        7000.0  # El gasto de $10k realmente cuesta $7k
    """
    _validate_tax_rate(tax_rate)
    return round(before_tax_cost * (1 - tax_rate), 2)


def after_tax_interest(interest_expense: float, tax_rate: float) -> float:
    """Calcula el costo de intereses después de impuestos.

    Los intereses son deducibles de impuestos (escudo fiscal de la deuda).
    Este es el principio fundamental detrás del WACC:
    Kd_after_tax = Kd × (1 - T)

    Args:
        interest_expense: Gasto de intereses.
        tax_rate: Tasa impositiva.

    Returns:
        Costo real de intereses.
    """
    return after_tax_cost(interest_expense, tax_rate)


# ---------------------------------------------------------------------------
# Disposición de Activos
# ---------------------------------------------------------------------------


def asset_disposal(
    original_cost: float,
    accumulated_depreciation: float,
    sale_price: float,
    tax_rate: float,
) -> AssetDisposalResult:
    """Calcula el impacto fiscal de vender un activo.

    Si el precio de venta > valor en libros → GANANCIA gravable.
    Si el precio de venta < valor en libros → PÉRDIDA deducible.

    Args:
        original_cost: Costo original del activo.
        accumulated_depreciation: Depreciación acumulada al momento de la venta.
        sale_price: Precio de venta del activo.
        tax_rate: Tasa impositiva.

    Returns:
        AssetDisposalResult con ganancia/pérdida y efectos fiscales.

    Examples:
        >>> asset_disposal(100000, 80000, 25000, 0.30)
        # Valor en libros = 20k, ganancia = 5k, tax = 1.5k
        # Net proceeds = 25k - 1.5k = 23.5k
    """
    _validate_tax_rate(tax_rate)

    book_value = original_cost - accumulated_depreciation
    gain_or_loss = sale_price - book_value

    is_gain = gain_or_loss >= 0
    tax_effect = gain_or_loss * tax_rate  # Positivo = impuesto, Negativo = beneficio

    net_proceeds = sale_price - tax_effect

    return AssetDisposalResult(
        sale_price=round(sale_price, 2),
        book_value_at_sale=round(book_value, 2),
        gain_or_loss=round(gain_or_loss, 2),
        tax_on_gain=round(tax_effect, 2),
        net_proceeds=round(net_proceeds, 2),
        is_gain=is_gain,
    )
