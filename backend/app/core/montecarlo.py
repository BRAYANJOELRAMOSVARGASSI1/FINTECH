"""
montecarlo.py — Simulación de Monte Carlo para Análisis de Riesgo.

La simulación de Monte Carlo estresa las variables de entrada
(inflación, costos, ingresos) miles de veces con distribuciones
probabilísticas para obtener la PROBABILIDAD de que un proyecto
sea rentable.

CONCEPTO CLAVE:
    Un VPN puntual dice "el proyecto vale X". Pero ¿qué tan seguro
    estás de esas proyecciones? Monte Carlo te da:
    - Probabilidad de VPN > 0 (probabilidad de éxito)
    - VPN en el percentil 5 (peor escenario razonable)
    - VPN en el percentil 95 (mejor escenario razonable)
    - Distribución completa para tomar decisiones informadas.

Implementación:
    - Usa numpy para vectorización → 10,000 simulaciones en <100ms.
    - Variables estresadas:
        * Inflación (distribución normal)
        * Costos de mantenimiento (distribución normal)
        * Ingresos/Revenue (distribución normal o triangular)
    - Resultados incluyen estadísticas descriptivas y percentiles.

References:
    - Damodaran — Applied Corporate Finance, Cap. 6 (Risk in Valuation)
    - Hertz, D.B. (1964) — "Risk Analysis in Capital Investment" (HBR)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class MonteCarloVariable:
    """Definición de una variable a estresar.

    Attributes:
        name: Nombre descriptivo de la variable.
        base_value: Valor base (esperado/puntual).
        std_dev: Desviación estándar (volatilidad).
        min_value: Valor mínimo permitido (clamp).
        max_value: Valor máximo permitido (clamp).
        distribution: Tipo de distribución ("normal", "triangular", "uniform").
    """

    name: str
    base_value: float
    std_dev: float
    min_value: float | None = None
    max_value: float | None = None
    distribution: str = "normal"


@dataclass(frozen=True, slots=True)
class MonteCarloStats:
    """Estadísticas descriptivas de la simulación."""

    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    percentile_5: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    percentile_95: float
    probability_positive: float  # P(VPN > 0)
    probability_negative: float  # P(VPN < 0)
    skewness: float
    kurtosis: float


@dataclass(frozen=True, slots=True)
class MonteCarloResult:
    """Resultado completo de la simulación de Monte Carlo."""

    iterations: int
    stats: MonteCarloStats
    histogram_data: list[float]  # VPN de cada simulación (para graficar)
    histogram_bins: list[float]  # Bordes de los bins del histograma
    histogram_counts: list[int]  # Frecuencia de cada bin
    variables_stressed: list[str]
    confidence_interval_90: tuple[float, float]
    confidence_interval_95: tuple[float, float]
    decision: str  # "HIGH_CONFIDENCE_ACCEPT", "MODERATE_RISK", "HIGH_RISK_REJECT"
    risk_assessment: str  # Explicación textual del riesgo


# ---------------------------------------------------------------------------
# Generación de Variables Aleatorias
# ---------------------------------------------------------------------------


def _generate_random_values(
    variable: MonteCarloVariable,
    n_iterations: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Genera valores aleatorios según la distribución especificada.

    Args:
        variable: Definición de la variable estocástica.
        n_iterations: Número de muestras a generar.
        rng: Generador de números aleatorios (reproducible con seed).

    Returns:
        Array de numpy con los valores generados.
    """
    if variable.distribution == "normal":
        values = rng.normal(variable.base_value, variable.std_dev, n_iterations)
    elif variable.distribution == "triangular":
        low = variable.min_value if variable.min_value is not None else (
            variable.base_value - 3 * variable.std_dev
        )
        high = variable.max_value if variable.max_value is not None else (
            variable.base_value + 3 * variable.std_dev
        )
        values = rng.triangular(low, variable.base_value, high, n_iterations)
    elif variable.distribution == "uniform":
        low = variable.min_value if variable.min_value is not None else (
            variable.base_value - variable.std_dev * 1.732
        )
        high = variable.max_value if variable.max_value is not None else (
            variable.base_value + variable.std_dev * 1.732
        )
        values = rng.uniform(low, high, n_iterations)
    else:
        raise ValueError(f"Distribución '{variable.distribution}' no soportada.")

    # Aplicar clamps si están definidos
    if variable.min_value is not None:
        values = np.maximum(values, variable.min_value)
    if variable.max_value is not None:
        values = np.minimum(values, variable.max_value)

    return values


# ---------------------------------------------------------------------------
# Simulación Principal
# ---------------------------------------------------------------------------


def run_npv_montecarlo(
    base_cash_flows: list[float],
    discount_rate: float,
    variables: list[MonteCarloVariable],
    cash_flow_impacts: dict[str, list[int]],
    n_iterations: int = 10_000,
    seed: int | None = 42,
    n_bins: int = 50,
) -> MonteCarloResult:
    """Ejecuta simulación de Monte Carlo sobre el VPN de un proyecto.

    Proceso:
    1. Para cada iteración:
       a. Genera valores aleatorios para cada variable estresada.
       b. Ajusta los flujos de caja base según esos valores.
       c. Calcula el VPN con los flujos ajustados.
    2. Calcula estadísticas sobre los N VPNs resultantes.

    Args:
        base_cash_flows: Flujos de caja base del proyecto (caso esperado).
        discount_rate: Tasa de descuento (WACC).
        variables: Lista de variables a estresar (inflación, costos, etc.).
        cash_flow_impacts: Diccionario que mapea nombre_variable → lista de
            índices de flujos de caja que afecta esa variable.
            Ej: {"inflation": [1, 2, 3, 4, 5]} (afecta años 1-5).
        n_iterations: Número de simulaciones (default: 10,000).
        seed: Semilla para reproducibilidad. None = aleatorio.
        n_bins: Número de bins para el histograma.

    Returns:
        MonteCarloResult con estadísticas completas y datos para visualización.

    Examples:
        >>> result = run_npv_montecarlo(
        ...     base_cash_flows=[-100000, 30000, 35000, 40000, 45000, 50000],
        ...     discount_rate=0.10,
        ...     variables=[
        ...         MonteCarloVariable("revenue_growth", 1.0, 0.15, 0.5, 1.5),
        ...         MonteCarloVariable("cost_inflation", 1.0, 0.05, 0.9, 1.3),
        ...     ],
        ...     cash_flow_impacts={
        ...         "revenue_growth": [1, 2, 3, 4, 5],
        ...         "cost_inflation": [1, 2, 3, 4, 5],
        ...     },
        ... )
        >>> print(f"P(VPN > 0) = {result.stats.probability_positive:.1%}")
    """
    if len(base_cash_flows) < 2:
        raise ValueError("Se requieren al menos 2 períodos de flujos de caja.")
    if n_iterations < 100:
        raise ValueError("Se requieren al menos 100 iteraciones para resultados significativos.")
    if discount_rate <= -1:
        raise ValueError("La tasa de descuento debe ser > -100%.")

    rng = np.random.default_rng(seed)
    base_cf = np.array(base_cash_flows, dtype=np.float64)
    n_periods = len(base_cash_flows)

    # Generar todas las variables aleatorias
    random_values: dict[str, np.ndarray] = {}
    for var in variables:
        random_values[var.name] = _generate_random_values(var, n_iterations, rng)

    # Simular VPNs
    npv_results = np.empty(n_iterations, dtype=np.float64)
    discount_factors = np.array([
        1 / (1 + discount_rate) ** t for t in range(n_periods)
    ])

    for i in range(n_iterations):
        cf_adjusted = base_cf.copy()

        # Aplicar cada variable a los flujos que afecta
        for var in variables:
            multiplier = random_values[var.name][i] / var.base_value
            affected_periods = cash_flow_impacts.get(var.name, [])
            for period_idx in affected_periods:
                if 0 <= period_idx < n_periods:
                    cf_adjusted[period_idx] *= multiplier

        # VPN vectorizado
        npv_results[i] = np.sum(cf_adjusted * discount_factors)

    # --- Estadísticas ---
    mean_npv = float(np.mean(npv_results))
    median_npv = float(np.median(npv_results))
    std_npv = float(np.std(npv_results))
    min_npv = float(np.min(npv_results))
    max_npv = float(np.max(npv_results))

    percentiles = np.percentile(npv_results, [5, 10, 25, 75, 90, 95])
    prob_positive = float(np.mean(npv_results > 0))
    prob_negative = float(np.mean(npv_results < 0))

    # Skewness y Kurtosis
    if std_npv > 0:
        skewness = float(np.mean(((npv_results - mean_npv) / std_npv) ** 3))
        kurtosis = float(np.mean(((npv_results - mean_npv) / std_npv) ** 4) - 3)
    else:
        skewness = 0.0
        kurtosis = 0.0

    stats = MonteCarloStats(
        mean=round(mean_npv, 2),
        median=round(median_npv, 2),
        std_dev=round(std_npv, 2),
        min_value=round(min_npv, 2),
        max_value=round(max_npv, 2),
        percentile_5=round(float(percentiles[0]), 2),
        percentile_10=round(float(percentiles[1]), 2),
        percentile_25=round(float(percentiles[2]), 2),
        percentile_75=round(float(percentiles[3]), 2),
        percentile_90=round(float(percentiles[4]), 2),
        percentile_95=round(float(percentiles[5]), 2),
        probability_positive=round(prob_positive, 4),
        probability_negative=round(prob_negative, 4),
        skewness=round(skewness, 4),
        kurtosis=round(kurtosis, 4),
    )

    # Histograma para visualización
    counts, bin_edges = np.histogram(npv_results, bins=n_bins)

    # Decisión basada en probabilidad
    if prob_positive >= 0.85:
        decision = "HIGH_CONFIDENCE_ACCEPT"
        risk_assessment = (
            f"El proyecto tiene una probabilidad de éxito del {prob_positive:.1%}. "
            f"Incluso en el peor escenario razonable (P5), el VPN es ${percentiles[0]:,.2f}. "
            f"Se recomienda ACEPTAR con alta confianza."
        )
    elif prob_positive >= 0.60:
        decision = "MODERATE_RISK"
        risk_assessment = (
            f"El proyecto tiene un {prob_positive:.1%} de probabilidad de éxito. "
            f"Existe un {prob_negative:.1%} de probabilidad de pérdida. "
            f"En el peor escenario (P5): ${percentiles[0]:,.2f}. "
            f"Se recomienda análisis adicional antes de decidir."
        )
    else:
        decision = "HIGH_RISK_REJECT"
        risk_assessment = (
            f"El proyecto tiene solo un {prob_positive:.1%} de probabilidad de éxito. "
            f"El riesgo de pérdida es del {prob_negative:.1%}. "
            f"Peor escenario (P5): ${percentiles[0]:,.2f}. "
            f"Se recomienda RECHAZAR o reestructurar significativamente."
        )

    return MonteCarloResult(
        iterations=n_iterations,
        stats=stats,
        histogram_data=npv_results.tolist(),
        histogram_bins=bin_edges.tolist(),
        histogram_counts=counts.tolist(),
        variables_stressed=[v.name for v in variables],
        confidence_interval_90=(round(float(percentiles[1]), 2), round(float(percentiles[4]), 2)),
        confidence_interval_95=(round(float(percentiles[0]), 2), round(float(percentiles[5]), 2)),
        decision=decision,
        risk_assessment=risk_assessment,
    )
