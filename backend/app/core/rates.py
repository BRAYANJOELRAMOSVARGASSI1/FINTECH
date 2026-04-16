"""
rates.py — Conversión Universal de Tasas de Interés.

Este módulo es el PUNTO DE ENTRADA obligatorio para cualquier tasa
que ingrese al sistema. Ningún cálculo se ejecuta con tasas nominales
directamente — todo se convierte a Tasa Efectiva Anual (TEA) primero.

Fórmulas implementadas:
    - TEA = (1 + i_nom / m)^m - 1
    - Fisher: (1 + r_real) = (1 + r_nom) / (1 + π)
    - Tasa periódica: (1 + TEA)^(1/m) - 1
    - Tasa continua: e^r - 1

Referencias:
    - Brealey, Myers & Allen — Principles of Corporate Finance
    - Damodaran — Investment Valuation (3rd Ed.)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPOUNDING_PERIODS: dict[str, int] = {
    "daily": 365,
    "weekly": 52,
    "biweekly": 26,
    "monthly": 12,
    "bimonthly": 6,
    "quarterly": 4,
    "semiannual": 2,
    "annual": 1,
    "continuous": 0,  # Señal especial para capitalización continua
}

# Límites de seguridad para validación
MAX_NOMINAL_RATE = 10.0  # 1000% — protección contra errores de entrada
MIN_RATE = -1.0  # -100% — piso teórico


# ---------------------------------------------------------------------------
# Data Classes para resultados estructurados
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class RateConversionResult:
    """Resultado de una conversión de tasa."""

    original_rate: float
    original_type: str
    effective_annual_rate: float
    periodic_rate: float | None = None
    periods_per_year: int | None = None

    @property
    def tea_percentage(self) -> float:
        """TEA expresada como porcentaje."""
        return round(self.effective_annual_rate * 100, 6)


@dataclass(frozen=True, slots=True)
class RateComparisonItem:
    """Un elemento dentro de la comparación de tasas."""

    label: str
    nominal_rate: float
    compounding: str
    effective_annual_rate: float
    rank: int = 0


@dataclass(frozen=True, slots=True)
class RateComparisonResult:
    """Resultado de comparar múltiples tasas."""

    items: list[RateComparisonItem] = field(default_factory=list)
    cheapest_label: str = ""
    most_expensive_label: str = ""
    spread_bps: float = 0.0  # Spread en basis points


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------


def _validate_rate(rate: float, name: str = "rate") -> None:
    """Valida que una tasa esté dentro de límites razonables.

    Args:
        rate: Tasa a validar (en decimal, ej: 0.18 para 18%).
        name: Nombre descriptivo para mensajes de error.

    Raises:
        ValueError: Si la tasa está fuera de rango o no es finita.
    """
    if not math.isfinite(rate):
        raise ValueError(f"{name} debe ser un número finito, recibido: {rate}")
    if rate < MIN_RATE:
        raise ValueError(
            f"{name} = {rate} está por debajo del piso teórico ({MIN_RATE}). "
            "Verifica que la tasa esté en formato decimal (ej: 0.18 para 18%)."
        )
    if rate > MAX_NOMINAL_RATE:
        raise ValueError(
            f"{name} = {rate} ({rate*100}%) excede el máximo permitido "
            f"({MAX_NOMINAL_RATE*100}%). ¿Ingresaste la tasa como porcentaje en vez de decimal?"
        )


def _validate_periods(periods: int) -> None:
    """Valida el número de períodos de capitalización."""
    if periods < 0:
        raise ValueError(f"Períodos de capitalización deben ser >= 0, recibido: {periods}")


def _resolve_compounding(compounding: str | int) -> int:
    """Resuelve el período de capitalización a un entero.

    Args:
        compounding: Nombre del período ("monthly", "quarterly", etc.) o número directo.

    Returns:
        Número de capitalizaciones por año.

    Raises:
        ValueError: Si el período no es reconocido.
    """
    if isinstance(compounding, int):
        _validate_periods(compounding)
        return compounding
    key = compounding.lower().strip()
    if key not in COMPOUNDING_PERIODS:
        valid = ", ".join(COMPOUNDING_PERIODS.keys())
        raise ValueError(f"Período '{compounding}' no reconocido. Válidos: {valid}")
    return COMPOUNDING_PERIODS[key]


# ---------------------------------------------------------------------------
# Funciones de Conversión — El corazón del sistema
# ---------------------------------------------------------------------------


def nominal_to_effective(nominal_rate: float, compounding: str | int) -> float:
    """Convierte una tasa nominal a Tasa Efectiva Anual (TEA).

    La tasa nominal por sí sola es ENGAÑOSA — no refleja el costo real
    del dinero porque ignora el efecto de la capitalización. Esta función
    revela el costo real.

    Fórmula: TEA = (1 + i_nom / m)^m - 1

    Para capitalización continua: TEA = e^(i_nom) - 1

    Args:
        nominal_rate: Tasa nominal anual en decimal (ej: 0.18 para 18%).
        compounding: Frecuencia de capitalización ("monthly", "quarterly", etc.)
            o número directo de períodos por año.

    Returns:
        Tasa Efectiva Anual (TEA) en decimal.

    Examples:
        >>> nominal_to_effective(0.18, "quarterly")  # 18% cap. trimestral
        0.192518...
        >>> nominal_to_effective(0.18, "monthly")    # 18% cap. mensual
        0.195618...
        >>> nominal_to_effective(0.18, "annual")     # 18% cap. anual = 18%
        0.18
        >>> nominal_to_effective(0.12, "continuous")  # Capitalización continua
        0.127496...
    """
    _validate_rate(nominal_rate, "nominal_rate")
    periods = _resolve_compounding(compounding)

    # Capitalización continua
    if periods == 0:
        return math.exp(nominal_rate) - 1

    # Caso trivial: capitalización anual = la tasa ya es efectiva
    if periods == 1:
        return nominal_rate

    periodic_rate = nominal_rate / periods
    return (1 + periodic_rate) ** periods - 1


def effective_to_nominal(effective_rate: float, compounding: str | int) -> float:
    """Convierte TEA a tasa nominal con la capitalización dada.

    Operación inversa de nominal_to_effective().

    Fórmula: i_nom = m * [(1 + TEA)^(1/m) - 1]

    Args:
        effective_rate: Tasa Efectiva Anual en decimal.
        compounding: Frecuencia de capitalización deseada.

    Returns:
        Tasa nominal anual en decimal.

    Examples:
        >>> effective_to_nominal(0.192519, "quarterly")
        0.18  (aproximadamente)
    """
    _validate_rate(effective_rate, "effective_rate")
    periods = _resolve_compounding(compounding)

    if effective_rate <= -1:
        raise ValueError("TEA debe ser > -100% para la conversión inversa.")

    # Capitalización continua
    if periods == 0:
        return math.log(1 + effective_rate)

    if periods == 1:
        return effective_rate

    periodic_rate = (1 + effective_rate) ** (1 / periods) - 1
    return periodic_rate * periods


def effective_to_periodic(effective_annual: float, periods_per_year: int) -> float:
    """Convierte TEA a tasa periódica equivalente.

    Útil para cálculos de cuotas mensuales, trimestrales, etc.

    Fórmula: i_per = (1 + TEA)^(1/m) - 1

    Args:
        effective_annual: TEA en decimal.
        periods_per_year: Número de períodos por año.

    Returns:
        Tasa periódica en decimal.

    Examples:
        >>> effective_to_periodic(0.12, 12)  # TEA 12% → tasa mensual
        0.009488...  (≈ 0.949% mensual, NO 1%)
    """
    _validate_rate(effective_annual, "effective_annual")
    if periods_per_year < 1:
        raise ValueError("periods_per_year debe ser >= 1")

    if effective_annual <= -1:
        raise ValueError("TEA debe ser > -100%.")

    return (1 + effective_annual) ** (1 / periods_per_year) - 1


def periodic_to_effective(periodic_rate: float, periods_per_year: int) -> float:
    """Convierte tasa periódica a TEA.

    Fórmula: TEA = (1 + i_per)^m - 1

    Args:
        periodic_rate: Tasa del período en decimal.
        periods_per_year: Número de períodos por año.

    Returns:
        TEA en decimal.
    """
    _validate_rate(periodic_rate, "periodic_rate")
    if periods_per_year < 1:
        raise ValueError("periods_per_year debe ser >= 1")

    return (1 + periodic_rate) ** periods_per_year - 1


def real_rate(nominal_rate: float, inflation_rate: float) -> float:
    """Calcula la tasa real usando la ecuación de Fisher.

    La tasa nominal incluye el efecto de la inflación. Esta función
    aísla el rendimiento REAL del dinero.

    Ecuación de Fisher exacta:
        (1 + r_real) = (1 + r_nominal) / (1 + π)
        r_real = (1 + r_nominal) / (1 + π) - 1

    Args:
        nominal_rate: Tasa nominal en decimal (ya convertida a efectiva idealmente).
        inflation_rate: Tasa de inflación en decimal.

    Returns:
        Tasa real en decimal.

    Examples:
        >>> real_rate(0.15, 0.05)  # Nominal 15%, inflación 5%
        0.095238...  (≈ 9.52%, NO 10%)

    Note:
        La aproximación r_real ≈ r_nom - π es IMPRECISA.
        Siempre usamos Fisher exacto.
    """
    _validate_rate(nominal_rate, "nominal_rate")
    _validate_rate(inflation_rate, "inflation_rate")

    if inflation_rate <= -1:
        raise ValueError("Inflación no puede ser <= -100%.")

    return (1 + nominal_rate) / (1 + inflation_rate) - 1


def nominal_rate_from_real(real_rate_value: float, inflation_rate: float) -> float:
    """Calcula la tasa nominal dada la tasa real e inflación (Fisher inverso).

    Fórmula: r_nom = (1 + r_real) * (1 + π) - 1

    Args:
        real_rate_value: Tasa real en decimal.
        inflation_rate: Tasa de inflación en decimal.

    Returns:
        Tasa nominal en decimal.
    """
    _validate_rate(real_rate_value, "real_rate_value")
    _validate_rate(inflation_rate, "inflation_rate")

    return (1 + real_rate_value) * (1 + inflation_rate) - 1


def compare_rates(
    rates: list[dict[str, float | str]],
    perspective: str = "borrower",
) -> RateComparisonResult:
    """Compara múltiples tasas convirtiéndolas todas a TEA.

    Este es el análisis que un CFO necesita cuando recibe múltiples
    ofertas de financiamiento con diferentes capitalizaciones.

    Args:
        rates: Lista de diccionarios con:
            - "label": Nombre descriptivo (ej: "Banco A")
            - "nominal_rate": Tasa nominal en decimal
            - "compounding": Frecuencia de capitalización
        perspective: "borrower" (menor TEA = mejor) o "investor" (mayor TEA = mejor).

    Returns:
        RateComparisonResult con ranking y spread.

    Examples:
        >>> compare_rates([
        ...     {"label": "Banco A", "nominal_rate": 0.18, "compounding": "annual"},
        ...     {"label": "Banco B", "nominal_rate": 0.18, "compounding": "quarterly"},
        ...     {"label": "Banco C", "nominal_rate": 0.175, "compounding": "monthly"},
        ... ], perspective="borrower")
    """
    if not rates:
        raise ValueError("Se requiere al menos una tasa para comparar.")
    if perspective not in ("borrower", "investor"):
        raise ValueError("perspective debe ser 'borrower' o 'investor'.")

    items: list[RateComparisonItem] = []
    for entry in rates:
        label = str(entry.get("label", f"Tasa {len(items) + 1}"))
        nominal = float(entry["nominal_rate"])
        compounding = entry["compounding"]
        tea = nominal_to_effective(nominal, compounding)

        items.append(
            RateComparisonItem(
                label=label,
                nominal_rate=nominal,
                compounding=str(compounding),
                effective_annual_rate=tea,
            )
        )

    # Ranking: para deudor, menor TEA es mejor (rank 1)
    reverse = perspective == "investor"
    sorted_items = sorted(items, key=lambda x: x.effective_annual_rate, reverse=reverse)

    ranked = []
    for idx, item in enumerate(sorted_items):
        ranked.append(
            RateComparisonItem(
                label=item.label,
                nominal_rate=item.nominal_rate,
                compounding=item.compounding,
                effective_annual_rate=item.effective_annual_rate,
                rank=idx + 1,
            )
        )

    # Spread entre la más cara y la más barata
    teas = [item.effective_annual_rate for item in ranked]
    spread_bps = (max(teas) - min(teas)) * 10_000  # Basis points

    return RateComparisonResult(
        items=ranked,
        cheapest_label=ranked[0].label if not reverse else ranked[-1].label,
        most_expensive_label=ranked[-1].label if not reverse else ranked[0].label,
        spread_bps=round(spread_bps, 2),
    )

def simple_interest_yield(annual_rate: float, years: float) -> float:
    """Calcula el rendimiento absoluto del interés simple.
    
    A diferencia del compuesto, el interés simple no reinvierte los intereses.
    Rendimiento = r * t
    """
    _validate_rate(annual_rate, "annual_rate")
    if years < 0:
        raise ValueError("El tiempo en años no puede ser negativo.")
    return annual_rate * years

def compare_simple_vs_compound(principal: float, annual_rate: float, years: float) -> dict[str, float]:
    """Compara el valor final obtenido por interés simple vs capitalización compuesta anual.
    
    Returns:
        dict con el valor final simple, compuesto y la diferencia absoluta.
    """
    if principal <= 0:
        raise ValueError("El capital inicial debe ser mayor a 0.")
        
    _validate_rate(annual_rate, "annual_rate")
    if years < 0:
        raise ValueError("El tiempo en años no puede ser negativo.")
        
    simple_fv = principal * (1 + (annual_rate * years))
    compound_fv = principal * ((1 + annual_rate) ** years)
    
    # Redondear para moneda
    simple_fv = round(simple_fv, 2)
    compound_fv = round(compound_fv, 2)
    
    return {
        "simple_future_value": simple_fv,
        "compound_future_value": compound_fv,
        "difference": round(compound_fv - simple_fv, 2)
    }

def wacc(
    equity: float,
    debt: float,
    cost_of_equity: float,
    cost_of_debt: float,
    tax_rate: float,
) -> float:
    """Calcula el Costo Promedio Ponderado de Capital (WACC).

    WACC = (E/(E+D)) * Ke + (D/(E+D)) * Kd * (1 - T)

    El WACC se usa como tasa de descuento para el VPN de proyectos.
    Refleja el costo real de cada dólar de capital considerando
    el mix de deuda/equity y el beneficio fiscal de la deuda.

    Args:
        equity: Valor de mercado del patrimonio (E).
        debt: Valor de mercado de la deuda (D).
        cost_of_equity: Costo del patrimonio (Ke) en decimal — usualmente CAPM.
        cost_of_debt: Costo de la deuda (Kd) en decimal — TEA de la deuda.
        tax_rate: Tasa impositiva corporativa (T) en decimal.

    Returns:
        WACC en decimal.

    Raises:
        ValueError: Si equity + debt = 0 o parámetros fuera de rango.
    """
    total = equity + debt
    if total <= 0:
        raise ValueError("La suma de equity + debt debe ser > 0.")
    if not (0 <= tax_rate < 1):
        raise ValueError(f"tax_rate debe estar en [0, 1), recibido: {tax_rate}")

    _validate_rate(cost_of_equity, "cost_of_equity")
    _validate_rate(cost_of_debt, "cost_of_debt")

    weight_equity = equity / total
    weight_debt = debt / total

    return (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))
