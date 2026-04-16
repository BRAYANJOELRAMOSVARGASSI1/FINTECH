"""
api/v1/valuation.py — Endpoints de valoración financiera.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.valuation import (
    free_cash_flow,
    full_valuation,
    internal_rate_of_return,
    net_present_value,
)
from app.schemas.valuation import (
    FCFRequest,
    FCFResponse,
    FullValuationRequest,
    FullValuationResponse,
    IRRRequest,
    IRRResponse,
    NPVRequest,
    NPVResponse,
    PaybackResponse,
    ProfitabilityIndexResponse,
)

router = APIRouter(prefix="/valuation", tags=["Valoración Financiera"])


@router.post(
    "/npv",
    response_model=NPVResponse,
    summary="Calcular Valor Presente Neto (VPN)",
    description="Descuenta flujos futuros al presente y determina si el proyecto crea valor.",
)
async def calculate_npv(request: NPVRequest) -> NPVResponse:
    """Calcula VPN con decisión automática."""
    try:
        result = net_present_value(request.cash_flows, request.discount_rate)

        explanation_parts = [
            f"Con una tasa de descuento del {request.discount_rate*100:.2f}%, ",
            f"el VPN del proyecto es ${result.npv:,.2f}. ",
        ]
        if result.decision == "ACCEPT":
            explanation_parts.append(
                "El proyecto CREA valor — los flujos futuros descontados "
                "superan la inversión inicial. Decisión: ACEPTAR."
            )
        elif result.decision == "REJECT":
            explanation_parts.append(
                "El proyecto DESTRUYE valor — la inversión no se recupera "
                "considerando el costo del dinero. Decisión: RECHAZAR."
            )
        else:
            explanation_parts.append(
                "El proyecto es financieramente indiferente — "
                "considere factores cualitativos."
            )

        return NPVResponse(
            npv=result.npv,
            npv_formatted=result.npv_formatted,
            discount_rate=result.discount_rate,
            periods=result.periods,
            decision=result.decision,
            present_values=result.present_values,
            explanation="".join(explanation_parts),
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/irr",
    response_model=IRRResponse,
    summary="Calcular Tasa Interna de Retorno (TIR)",
    description="Encuentra la tasa que hace VPN = 0. Compara con hurdle rate para decisión.",
)
async def calculate_irr(request: IRRRequest) -> IRRResponse:
    """Calcula TIR con decisión automática."""
    try:
        result = internal_rate_of_return(request.cash_flows, request.hurdle_rate)

        if not result.converged:
            explanation = (
                "La TIR no convergió. Esto puede ocurrir si los flujos no "
                "cambian de signo o si hay múltiples TIRs. Considere usar "
                "el VPN como métrica principal."
            )
        elif result.decision == "ACCEPT":
            explanation = (
                f"TIR = {result.irr*100:.4f}% > Hurdle Rate = {request.hurdle_rate*100:.2f}%. "
                f"El rendimiento del proyecto supera el costo de oportunidad. ACEPTAR."
            )
        elif result.decision == "REJECT":
            explanation = (
                f"TIR = {result.irr*100:.4f}% < Hurdle Rate = {request.hurdle_rate*100:.2f}%. "
                f"El rendimiento no compensa el riesgo. RECHAZAR."
            )
        else:
            explanation = (
                f"TIR = {result.irr*100:.4f}%. No se proporcionó hurdle rate para decisión."
            )

        return IRRResponse(
            irr=result.irr,
            irr_pct=result.irr_percentage,
            converged=result.converged,
            hurdle_rate=result.hurdle_rate,
            decision=result.decision,
            explanation=explanation,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/fcf",
    response_model=FCFResponse,
    summary="Calcular Flujo de Caja Libre (FCF)",
    description="Genera el FCF período a período considerando impuestos y depreciación.",
)
async def calculate_fcf(request: FCFRequest) -> FCFResponse:
    """Calcula FCF."""
    try:
        n = len(request.revenue)
        for field_name, field_val in [
            ("operating_expenses", request.operating_expenses),
            ("capex", request.capex),
            ("depreciation", request.depreciation),
        ]:
            if len(field_val) != n:
                raise ValueError(
                    f"{field_name} tiene {len(field_val)} elementos, "
                    f"pero revenue tiene {n}. Deben ser iguales."
                )

        fcf = free_cash_flow(
            revenue=request.revenue,
            operating_expenses=request.operating_expenses,
            capex=request.capex,
            tax_rate=request.tax_rate,
            depreciation=request.depreciation,
            working_capital_changes=request.working_capital_changes,
        )

        return FCFResponse(
            free_cash_flows=fcf,
            total_fcf=round(sum(fcf), 2),
            periods=n,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/full",
    response_model=FullValuationResponse,
    summary="Valoración completa del proyecto",
    description="Ejecuta VPN + TIR + Payback + PI en una sola llamada.",
)
async def full_valuation_endpoint(request: FullValuationRequest) -> FullValuationResponse:
    """Valoración integral."""
    try:
        result = full_valuation(
            cash_flows=request.cash_flows,
            discount_rate=request.discount_rate,
            hurdle_rate=request.hurdle_rate,
        )

        # Build sub-responses
        npv_resp = NPVResponse(
            npv=result.npv.npv,
            npv_formatted=result.npv.npv_formatted,
            discount_rate=result.npv.discount_rate,
            periods=result.npv.periods,
            decision=result.npv.decision,
            present_values=result.npv.present_values,
            explanation=f"VPN = ${result.npv.npv:,.2f} → {result.npv.decision}",
        )

        irr_explanation = "No convergió" if not result.irr.converged else (
            f"TIR = {result.irr.irr*100:.4f}%"
        )
        irr_resp = IRRResponse(
            irr=result.irr.irr,
            irr_pct=result.irr.irr_percentage,
            converged=result.irr.converged,
            hurdle_rate=result.irr.hurdle_rate,
            decision=result.irr.decision,
            explanation=irr_explanation,
        )

        payback_resp = PaybackResponse(
            simple_payback=result.payback.simple_payback,
            discounted_payback=result.payback.discounted_payback,
            discount_rate=result.payback.discount_rate,
            cumulative_flows=result.payback.cumulative_flows,
            cumulative_pv_flows=result.payback.cumulative_pv_flows,
        )

        pi_resp = ProfitabilityIndexResponse(
            pi=result.profitability_index.pi,
            decision=result.profitability_index.decision,
        )

        # Overall recommendation
        signals = []
        if result.npv.decision == "ACCEPT":
            signals.append("VPN+")
        if result.irr.decision == "ACCEPT":
            signals.append("TIR+")
        if result.profitability_index.decision == "ACCEPT":
            signals.append("PI+")

        if len(signals) >= 2:
            overall = "ACCEPT — Mayoría de indicadores favorables"
        elif len(signals) == 1:
            overall = "REVIEW — Señales mixtas, analizar con mayor detalle"
        else:
            overall = "REJECT — Indicadores desfavorables"

        return FullValuationResponse(
            npv=npv_resp,
            irr=irr_resp,
            payback=payback_resp,
            profitability_index=pi_resp,
            cash_flows=result.cash_flows,
            discount_rate=result.discount_rate,
            overall_recommendation=overall,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
