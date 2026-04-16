"""
api/v1/analysis.py — Endpoints de análisis CAPEX vs OPEX y Monte Carlo.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.capex_opex import (
    CapexInput,
    OpexInput,
    compare_capex_vs_opex,
)
from app.core.montecarlo import MonteCarloVariable, run_npv_montecarlo
from app.core.taxes import DepreciationMethod
from app.schemas.capex_opex import (
    CapexAnalysisResponse,
    CapexVsOpexRequest,
    CapexVsOpexResponse,
    MonteCarloRequest,
    MonteCarloResponse,
    MonteCarloStatsResponse,
    OpexAnalysisResponse,
    SensitivityPointResponse,
)

router = APIRouter(prefix="/analysis", tags=["Análisis Financiero"])


@router.post(
    "/capex-vs-opex",
    response_model=CapexVsOpexResponse,
    summary="Análisis CAPEX vs OPEX",
    description=(
        "Compara la compra de un activo (CAPEX) contra un gasto "
        "operativo recurrente (OPEX). Incluye depreciación, escudos "
        "fiscales, valor de salvamento y análisis de sensibilidad."
    ),
)
async def capex_vs_opex(request: CapexVsOpexRequest) -> CapexVsOpexResponse:
    """Análisis comparativo CAPEX vs OPEX."""
    try:
        # Map enum values to core DepreciationMethod
        dep_method_map = {
            "straight_line": DepreciationMethod.STRAIGHT_LINE,
            "declining_balance": DepreciationMethod.DECLINING_BALANCE,
            "sum_of_years_digits": DepreciationMethod.SUM_OF_YEARS_DIGITS,
        }

        capex_input = CapexInput(
            initial_investment=request.capex.initial_investment,
            useful_life_years=request.capex.useful_life_years,
            salvage_value=request.capex.salvage_value,
            annual_maintenance=request.capex.annual_maintenance,
            tax_rate=request.capex.tax_rate,
            depreciation_method=dep_method_map[request.capex.depreciation_method.value],
            maintenance_growth_rate=request.capex.maintenance_growth_rate,
        )

        opex_input = OpexInput(
            annual_cost=request.opex.annual_cost,
            contract_years=request.opex.contract_years,
            tax_rate=request.opex.tax_rate,
            inflation_rate=request.opex.inflation_rate,
            setup_cost=request.opex.setup_cost,
        )

        result = compare_capex_vs_opex(
            capex=capex_input,
            opex=opex_input,
            wacc=request.wacc,
            run_sensitivity=request.run_sensitivity,
        )

        # Build response
        capex_resp = CapexAnalysisResponse(
            cash_flows=result.capex.cash_flows,
            depreciation_schedule=result.capex.depreciation_schedule,
            tax_shields=result.capex.tax_shields,
            maintenance_costs=result.capex.maintenance_costs,
            salvage_net_proceeds=result.capex.salvage_net_proceeds,
            total_cost_nominal=result.capex.total_cost_nominal,
            npv_cost=result.capex.npv_cost,
            year_labels=result.capex.year_labels,
        )

        opex_resp = OpexAnalysisResponse(
            cash_flows=result.opex.cash_flows,
            annual_costs_nominal=result.opex.annual_costs_nominal,
            tax_savings=result.opex.tax_savings,
            total_cost_nominal=result.opex.total_cost_nominal,
            npv_cost=result.opex.npv_cost,
            year_labels=result.opex.year_labels,
        )

        sensitivity = [
            SensitivityPointResponse(
                variable_name=sp.variable_name,
                variation_pct=sp.variation_pct,
                capex_npv=sp.capex_npv,
                opex_npv=sp.opex_npv,
                recommendation=sp.recommendation,
            )
            for sp in result.sensitivity
        ]

        return CapexVsOpexResponse(
            capex=capex_resp,
            opex=opex_resp,
            npv_advantage=result.npv_advantage,
            recommendation=result.recommendation,
            explanation=result.explanation,
            wacc_used=result.wacc_used,
            sensitivity=sensitivity,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.post(
    "/montecarlo",
    response_model=MonteCarloResponse,
    summary="Simulación de Monte Carlo",
    description=(
        "Ejecuta N simulaciones estresando variables de entrada "
        "para obtener la probabilidad de éxito del proyecto."
    ),
)
async def montecarlo_simulation(request: MonteCarloRequest) -> MonteCarloResponse:
    """Ejecuta simulación de Monte Carlo sobre VPN."""
    try:
        variables = [
            MonteCarloVariable(
                name=v.name,
                base_value=v.base_value,
                std_dev=v.std_dev,
                min_value=v.min_value,
                max_value=v.max_value,
                distribution=v.distribution.value,
            )
            for v in request.variables
        ]

        result = run_npv_montecarlo(
            base_cash_flows=request.cash_flows,
            discount_rate=request.discount_rate,
            variables=variables,
            cash_flow_impacts=request.cash_flow_impacts,
            n_iterations=request.iterations,
            seed=request.seed,
        )

        stats = MonteCarloStatsResponse(
            mean=result.stats.mean,
            median=result.stats.median,
            std_dev=result.stats.std_dev,
            min_value=result.stats.min_value,
            max_value=result.stats.max_value,
            percentile_5=result.stats.percentile_5,
            percentile_10=result.stats.percentile_10,
            percentile_25=result.stats.percentile_25,
            percentile_75=result.stats.percentile_75,
            percentile_90=result.stats.percentile_90,
            percentile_95=result.stats.percentile_95,
            probability_positive=result.stats.probability_positive,
            probability_negative=result.stats.probability_negative,
            skewness=result.stats.skewness,
            kurtosis=result.stats.kurtosis,
        )

        return MonteCarloResponse(
            iterations=result.iterations,
            stats=stats,
            histogram_bins=result.histogram_bins,
            histogram_counts=result.histogram_counts,
            variables_stressed=result.variables_stressed,
            confidence_interval_90=list(result.confidence_interval_90),
            confidence_interval_95=list(result.confidence_interval_95),
            decision=result.decision,
            risk_assessment=result.risk_assessment,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
