"""
api/v1/rates.py — Endpoints de conversión y comparación de tasas.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.rates import (
    compare_rates,
    nominal_to_effective,
    effective_to_periodic,
    real_rate,
    wacc as calc_wacc,
)
from app.schemas.rates import (
    FisherRateRequest,
    FisherRateResponse,
    RateComparisonRequest,
    RateComparisonResponse,
    RateComparisonItemResponse,
    RateConversionRequest,
    RateConversionResponse,
    WACCRequest,
    WACCResponse,
)

router = APIRouter(prefix="/rates", tags=["Tasas de Interés"])


@router.post(
    "/convert",
    response_model=RateConversionResponse,
    summary="Convertir tasa nominal a TEA",
    description=(
        "Convierte una tasa nominal con capitalización específica "
        "a Tasa Efectiva Anual (TEA). Fundamental para comparar "
        "ofertas de financiamiento con diferentes capitalizaciones."
    ),
)
async def convert_rate(request: RateConversionRequest) -> RateConversionResponse:
    """Convierte tasa nominal → TEA."""
    try:
        tea = nominal_to_effective(request.nominal_rate, request.compounding.value)
        periodic = effective_to_periodic(tea, _get_periods(request.compounding.value))

        return RateConversionResponse(
            original_nominal_rate=request.nominal_rate,
            compounding=request.compounding.value,
            effective_annual_rate=round(tea, 8),
            effective_annual_rate_pct=round(tea * 100, 4),
            periodic_rate=round(periodic, 8),
            explanation=(
                f"Una tasa nominal del {request.nominal_rate*100:.2f}% capitalizable "
                f"{request.compounding.value} equivale a una TEA del {tea*100:.4f}%. "
                f"La tasa periódica es {periodic*100:.4f}%."
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/compare",
    response_model=RateComparisonResponse,
    summary="Comparar múltiples tasas",
    description=(
        "Recibe N tasas con diferentes capitalizaciones, las convierte "
        "todas a TEA, y las ordena de mejor a peor según la perspectiva."
    ),
)
async def compare_rates_endpoint(request: RateComparisonRequest) -> RateComparisonResponse:
    """Compara múltiples tasas convertidas a TEA."""
    try:
        rates_input = [
            {
                "label": r.label,
                "nominal_rate": r.nominal_rate,
                "compounding": r.compounding.value,
            }
            for r in request.rates
        ]
        result = compare_rates(rates_input, request.perspective.value)

        items = [
            RateComparisonItemResponse(
                rank=item.rank,
                label=item.label,
                nominal_rate=item.nominal_rate,
                compounding=item.compounding,
                effective_annual_rate=round(item.effective_annual_rate, 8),
                effective_annual_rate_pct=round(item.effective_annual_rate * 100, 4),
            )
            for item in result.items
        ]

        perspective_text = (
            "Para el DEUDOR, la mejor opción es la de menor TEA."
            if request.perspective.value == "borrower"
            else "Para el INVERSOR, la mejor opción es la de mayor TEA."
        )

        return RateComparisonResponse(
            perspective=request.perspective.value,
            items=items,
            cheapest_label=result.cheapest_label,
            most_expensive_label=result.most_expensive_label,
            spread_bps=result.spread_bps,
            recommendation=(
                f"{perspective_text} La mejor opción es '{result.items[0].label}' "
                f"con TEA de {result.items[0].effective_annual_rate*100:.4f}%. "
                f"Spread total: {result.spread_bps:.2f} bps."
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/fisher",
    response_model=FisherRateResponse,
    summary="Calcular tasa real (Fisher)",
    description="Aísla el rendimiento real descontando la inflación.",
)
async def fisher_rate(request: FisherRateRequest) -> FisherRateResponse:
    """Ecuación de Fisher: tasa real."""
    try:
        r_real = real_rate(request.nominal_rate, request.inflation_rate)
        return FisherRateResponse(
            nominal_rate=request.nominal_rate,
            inflation_rate=request.inflation_rate,
            real_rate=round(r_real, 8),
            real_rate_pct=round(r_real * 100, 4),
            explanation=(
                f"Con una tasa nominal del {request.nominal_rate*100:.2f}% "
                f"y una inflación del {request.inflation_rate*100:.2f}%, "
                f"el rendimiento REAL es {r_real*100:.4f}%. "
                f"Nota: La aproximación simple (nominal - inflación = "
                f"{(request.nominal_rate - request.inflation_rate)*100:.2f}%) "
                f"es IMPRECISA. Fisher exacto da {r_real*100:.4f}%."
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/wacc",
    response_model=WACCResponse,
    summary="Calcular WACC",
    description="Costo Promedio Ponderado de Capital.",
)
async def calculate_wacc(request: WACCRequest) -> WACCResponse:
    """Calcula WACC."""
    try:
        wacc_value = calc_wacc(
            equity=request.equity,
            debt=request.debt,
            cost_of_equity=request.cost_of_equity,
            cost_of_debt=request.cost_of_debt,
            tax_rate=request.tax_rate,
        )
        total = request.equity + request.debt
        w_e = request.equity / total
        w_d = request.debt / total
        kd_at = request.cost_of_debt * (1 - request.tax_rate)

        return WACCResponse(
            wacc=round(wacc_value, 8),
            wacc_pct=round(wacc_value * 100, 4),
            weight_equity=round(w_e, 4),
            weight_debt=round(w_d, 4),
            cost_of_equity=request.cost_of_equity,
            cost_of_debt_after_tax=round(kd_at, 6),
            explanation=(
                f"WACC = {w_e:.2%} × {request.cost_of_equity*100:.2f}% + "
                f"{w_d:.2%} × {request.cost_of_debt*100:.2f}% × (1 - {request.tax_rate*100:.0f}%) "
                f"= {wacc_value*100:.4f}%. "
                f"Este es el costo mínimo que un proyecto debe superar para crear valor."
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


def _get_periods(compounding: str) -> int:
    """Helper para obtener períodos por año."""
    from app.core.rates import COMPOUNDING_PERIODS
    return COMPOUNDING_PERIODS.get(compounding, 1) or 1
