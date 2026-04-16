"""
test_capex_opex.py — Tests para el análisis CAPEX vs OPEX.
"""

import pytest

from app.core.capex_opex import (
    CapexInput,
    OpexInput,
    analyze_capex,
    analyze_opex,
    compare_capex_vs_opex,
)
from app.core.taxes import DepreciationMethod


class TestAnalyzeCapex:
    """Tests del análisis CAPEX."""

    def test_cash_flows_length(self):
        """Flujos = vida_útil + 1 (incluye año 0)."""
        capex = CapexInput(
            initial_investment=500_000,
            useful_life_years=5,
            salvage_value=50_000,
            annual_maintenance=20_000,
            tax_rate=0.30,
        )
        result = analyze_capex(capex, 0.10)
        assert len(result.cash_flows) == 6  # Año 0 + 5 años

    def test_first_flow_negative(self):
        """Primer flujo = inversión negativa."""
        capex = CapexInput(
            initial_investment=100_000,
            useful_life_years=3,
            salvage_value=10_000,
            annual_maintenance=5_000,
            tax_rate=0.25,
        )
        result = analyze_capex(capex, 0.10)
        assert result.cash_flows[0] == -100_000

    def test_tax_shields_positive(self):
        """Escudos fiscales deben ser positivos."""
        capex = CapexInput(
            initial_investment=200_000,
            useful_life_years=5,
            salvage_value=20_000,
            annual_maintenance=10_000,
            tax_rate=0.30,
        )
        result = analyze_capex(capex, 0.10)
        assert all(s > 0 for s in result.tax_shields)


class TestAnalyzeOpex:
    """Tests del análisis OPEX."""

    def test_cash_flows_all_negative(self):
        """Todos los flujos OPEX deben ser ≤ 0 (son costos)."""
        opex = OpexInput(
            annual_cost=50_000,
            contract_years=5,
            tax_rate=0.30,
        )
        result = analyze_opex(opex, 0.10)
        assert all(cf <= 0 for cf in result.cash_flows)

    def test_inflation_increases_costs(self):
        """Con inflación, costos nominales deben crecer."""
        opex = OpexInput(
            annual_cost=50_000,
            contract_years=5,
            tax_rate=0.30,
            inflation_rate=0.05,
        )
        result = analyze_opex(opex, 0.10)
        costs = result.annual_costs_nominal
        assert all(costs[i] <= costs[i + 1] for i in range(len(costs) - 1))


class TestCompareCapexVsOpex:
    """Tests de la comparación completa."""

    def test_produces_recommendation(self):
        """Debe producir una recomendación válida."""
        capex = CapexInput(
            initial_investment=500_000,
            useful_life_years=5,
            salvage_value=50_000,
            annual_maintenance=20_000,
            tax_rate=0.30,
        )
        opex = OpexInput(
            annual_cost=120_000,
            contract_years=5,
            tax_rate=0.30,
            inflation_rate=0.03,
        )
        result = compare_capex_vs_opex(capex, opex, 0.10)
        assert result.recommendation in ("CAPEX", "OPEX", "INDIFFERENT")
        assert len(result.explanation) > 0

    def test_sensitivity_analysis(self):
        """Genera puntos de sensibilidad."""
        capex = CapexInput(
            initial_investment=200_000,
            useful_life_years=5,
            salvage_value=20_000,
            annual_maintenance=15_000,
            tax_rate=0.25,
        )
        opex = OpexInput(
            annual_cost=50_000,
            contract_years=5,
            tax_rate=0.25,
            inflation_rate=0.04,
        )
        result = compare_capex_vs_opex(capex, opex, 0.10, run_sensitivity=True)
        assert len(result.sensitivity) > 0

    def test_no_sensitivity(self):
        """Se puede desactivar la sensibilidad."""
        capex = CapexInput(
            initial_investment=100_000,
            useful_life_years=3,
            salvage_value=10_000,
            annual_maintenance=5_000,
            tax_rate=0.30,
        )
        opex = OpexInput(
            annual_cost=40_000,
            contract_years=3,
            tax_rate=0.30,
        )
        result = compare_capex_vs_opex(capex, opex, 0.10, run_sensitivity=False)
        assert len(result.sensitivity) == 0
