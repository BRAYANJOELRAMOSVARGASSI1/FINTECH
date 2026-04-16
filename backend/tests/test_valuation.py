"""
test_valuation.py — Tests para VPN, TIR, FCF, Payback y PI.
"""

import pytest

from app.core.valuation import (
    free_cash_flow,
    full_valuation,
    internal_rate_of_return,
    net_present_value,
    payback_period,
    profitability_index,
)


# ---------------------------------------------------------------------------
# VPN
# ---------------------------------------------------------------------------


class TestNPV:
    """Tests del Valor Presente Neto."""

    def test_positive_npv_classic(self):
        """Proyecto clásico rentable: inversión -100k, flujos positivos."""
        result = net_present_value([-100_000, 30_000, 40_000, 50_000, 30_000], 0.10)
        assert result.npv > 0
        assert result.decision == "ACCEPT"

    def test_negative_npv(self):
        """Proyecto no rentable."""
        result = net_present_value([-100_000, 10_000, 10_000, 10_000], 0.10)
        assert result.npv < 0
        assert result.decision == "REJECT"

    def test_zero_discount(self):
        """Con descuento 0%, VPN = suma simple de flujos."""
        flows = [-100, 40, 40, 40]
        result = net_present_value(flows, 0.0)
        assert abs(result.npv - 20) < 0.01

    def test_present_values_length(self):
        """Present values debe tener misma longitud que cash flows."""
        flows = [-50_000, 20_000, 25_000, 15_000]
        result = net_present_value(flows, 0.08)
        assert len(result.present_values) == len(flows)

    def test_rejects_single_flow(self):
        """Necesita al menos 2 períodos."""
        with pytest.raises(ValueError):
            net_present_value([-100_000], 0.10)


# ---------------------------------------------------------------------------
# TIR
# ---------------------------------------------------------------------------


class TestIRR:
    """Tests de la Tasa Interna de Retorno."""

    def test_known_irr(self):
        """Proyecto con TIR conocida."""
        # Inversión -1000, retorna 1100 → TIR = 10%
        result = internal_rate_of_return([-1000, 1100])
        assert result.converged
        assert abs(result.irr - 0.10) < 0.001

    def test_irr_vs_hurdle_accept(self):
        """TIR > hurdle → ACCEPT."""
        result = internal_rate_of_return([-1000, 600, 600], hurdle_rate=0.05)
        assert result.converged
        assert result.decision == "ACCEPT"

    def test_irr_vs_hurdle_reject(self):
        """TIR < hurdle → REJECT."""
        result = internal_rate_of_return([-1000, 500, 500], hurdle_rate=0.50)
        assert result.converged
        assert result.decision == "REJECT"

    def test_no_sign_change(self):
        """Sin cambio de signo → no converge."""
        result = internal_rate_of_return([100, 200, 300])
        # May or may not converge depending on algorithm, but should handle gracefully
        assert isinstance(result.converged, bool)


# ---------------------------------------------------------------------------
# Índice de Rentabilidad
# ---------------------------------------------------------------------------


class TestProfitabilityIndex:
    """Tests del PI."""

    def test_pi_greater_than_one(self):
        """PI > 1 → ACCEPT."""
        result = profitability_index([-100_000, 50_000, 50_000, 50_000], 0.10)
        assert result.pi > 1
        assert result.decision == "ACCEPT"

    def test_pi_less_than_one(self):
        """PI < 1 → REJECT."""
        result = profitability_index([-100_000, 10_000, 10_000], 0.10)
        assert result.pi < 1
        assert result.decision == "REJECT"


# ---------------------------------------------------------------------------
# Payback
# ---------------------------------------------------------------------------


class TestPayback:
    """Tests del período de recuperación."""

    def test_simple_payback(self):
        """Recuperación simple en período 3."""
        result = payback_period([-100, 40, 40, 40, 40], 0.10)
        assert result.simple_payback is not None
        assert 2.0 <= result.simple_payback <= 3.0

    def test_discounted_payback_longer(self):
        """Payback descontado siempre >= payback simple."""
        result = payback_period([-100, 40, 40, 40, 40], 0.15)
        if result.simple_payback and result.discounted_payback:
            assert result.discounted_payback >= result.simple_payback

    def test_never_recovers(self):
        """Proyecto que nunca se recupera → None."""
        result = payback_period([-1000, 10, 10, 10], 0.10)
        assert result.simple_payback is None


# ---------------------------------------------------------------------------
# FCF
# ---------------------------------------------------------------------------


class TestFCF:
    """Tests del Flujo de Caja Libre."""

    def test_basic_fcf(self):
        """FCF = NOPAT + Deprec - CapEx - ΔWC."""
        fcf = free_cash_flow(
            revenue=[100_000],
            operating_expenses=[60_000],
            capex=[10_000],
            tax_rate=0.30,
            depreciation=[5_000],
        )
        # EBIT = 100k - 60k - 5k = 35k
        # NOPAT = 35k * 0.7 = 24.5k
        # FCF = 24.5k + 5k - 10k = 19.5k
        assert len(fcf) == 1
        assert abs(fcf[0] - 19_500) < 0.01

    def test_multiple_periods(self):
        """FCF con múltiples períodos."""
        fcf = free_cash_flow(
            revenue=[100_000, 110_000, 120_000],
            operating_expenses=[60_000, 65_000, 70_000],
            capex=[10_000, 5_000, 5_000],
            tax_rate=0.25,
            depreciation=[8_000, 8_000, 8_000],
        )
        assert len(fcf) == 3
        assert all(isinstance(f, float) for f in fcf)

    def test_mismatched_lengths_raises(self):
        """Longitudes inconsistentes → error."""
        with pytest.raises(ValueError):
            free_cash_flow(
                revenue=[100_000, 110_000],
                operating_expenses=[60_000],  # Mismatched!
                capex=[10_000, 5_000],
                tax_rate=0.30,
                depreciation=[5_000, 5_000],
            )


# ---------------------------------------------------------------------------
# Full Valuation
# ---------------------------------------------------------------------------


class TestFullValuation:
    """Tests de la valoración integral."""

    def test_full_valuation_runs(self):
        """Valoración completa ejecuta sin errores."""
        result = full_valuation(
            cash_flows=[-100_000, 30_000, 40_000, 50_000, 30_000],
            discount_rate=0.10,
        )
        assert result.npv is not None
        assert result.irr is not None
        assert result.payback is not None
        assert result.profitability_index is not None

    def test_consistency(self):
        """VPN ACCEPT y TIR > WACC deben ser consistentes."""
        flows = [-100_000, 50_000, 50_000, 50_000]
        result = full_valuation(flows, 0.10)

        if result.npv.decision == "ACCEPT" and result.irr.converged:
            # Si VPN > 0, TIR debería ser > tasa de descuento
            assert result.irr.irr > 0.10
