"""
api/v1/amortization.py — Endpoints de tablas de amortización.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.amortization import (
    american_amortization,
    compare_amortization_systems,
    french_amortization,
    german_amortization,
)
from app.schemas.amortization import (
    AmortizationCompareRequest,
    AmortizationCompareResponse,
    AmortizationRequest,
    AmortizationRowResponse,
    AmortizationTableResponse,
)

router = APIRouter(prefix="/amortization", tags=["Tablas de Amortización"])


def _table_to_response(table) -> AmortizationTableResponse:
    """Convierte AmortizationTable del core a response schema."""
    rows = [
        AmortizationRowResponse(
            period=row.period,
            payment=row.payment,
            interest=row.interest,
            principal=row.principal,
            balance=row.balance,
        )
        for row in table.rows
    ]
    summary = table.summary()
    return AmortizationTableResponse(
        system=table.system,
        principal_amount=table.principal,
        annual_rate=table.annual_rate,
        annual_rate_pct=round(table.annual_rate * 100, 4),
        periodic_rate=table.periodic_rate,
        total_periods=table.total_periods,
        total_paid=table.total_paid,
        total_interest=table.total_interest,
        interest_ratio=table.interest_ratio,
        first_payment=summary["first_payment"],
        last_payment=summary["last_payment"],
        rows=rows,
    )


@router.post(
    "/schedule",
    response_model=AmortizationTableResponse,
    summary="Generar tabla de amortización",
    description="Genera la tabla completa período a período.",
)
async def generate_schedule(request: AmortizationRequest) -> AmortizationTableResponse:
    """Genera tabla de amortización según el sistema elegido."""
    try:
        amort_fn = {
            "french": french_amortization,
            "german": german_amortization,
            "american": american_amortization,
        }

        fn = amort_fn.get(request.system.value)
        if fn is None:
            raise ValueError(f"Sistema '{request.system.value}' no soportado.")

        table = fn(
            principal=request.principal,
            annual_rate=request.annual_rate,
            total_periods=request.total_periods,
            periods_per_year=request.periods_per_year,
        )

        return _table_to_response(table)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/compare",
    response_model=AmortizationCompareResponse,
    summary="Comparar tres sistemas de amortización",
    description="Genera y compara Francés, Alemán y Americano.",
)
async def compare_systems(request: AmortizationCompareRequest) -> AmortizationCompareResponse:
    """Compara los tres sistemas para los mismos parámetros."""
    try:
        tables = compare_amortization_systems(
            principal=request.principal,
            annual_rate=request.annual_rate,
            total_periods=request.total_periods,
            periods_per_year=request.periods_per_year,
        )

        french_resp = _table_to_response(tables["french"])
        german_resp = _table_to_response(tables["german"])
        american_resp = _table_to_response(tables["american"])

        # El más barato es el que paga menos intereses totales
        systems = {
            "french": french_resp.total_interest,
            "german": german_resp.total_interest,
            "american": american_resp.total_interest,
        }
        cheapest = min(systems, key=systems.get)

        recommendation = (
            f"El sistema {cheapest.upper()} es el más económico en intereses totales: "
            f"${systems[cheapest]:,.2f}. "
            f"Francés: ${systems['french']:,.2f} | "
            f"Alemán: ${systems['german']:,.2f} | "
            f"Americano: ${systems['american']:,.2f}. "
            f"Sin embargo, el Sistema Alemán tiene cuotas iniciales más altas, "
            f"y el Americano concentra el capital al final (mayor riesgo)."
        )

        return AmortizationCompareResponse(
            french=french_resp,
            german=german_resp,
            american=american_resp,
            cheapest_system=cheapest,
            recommendation=recommendation,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
