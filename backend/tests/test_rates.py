"""
test_rates.py — Tests para el motor de conversión de tasas.

Cada test valida contra resultados conocidos de libros de texto
de finanzas corporativas y calculadoras financieras.
"""

import math

import pytest

from app.core.rates import (
    compare_rates,
    effective_to_nominal,
    effective_to_periodic,
    nominal_rate_from_real,
    nominal_to_effective,
    periodic_to_effective,
    real_rate,
    wacc,
)


# ---------------------------------------------------------------------------
# nominal_to_effective
# ---------------------------------------------------------------------------


class TestNominalToEffective:
    """Tests de conversión nominal → TEA."""

    def test_18pct_quarterly(self):
        """18% nominal cap. trimestral → TEA = 19.2519%."""
        tea = nominal_to_effective(0.18, "quarterly")
        assert round(tea, 6) == 0.192519

    def test_18pct_monthly(self):
        """18% nominal cap. mensual → TEA > 19.25%."""
        tea = nominal_to_effective(0.18, "monthly")
        assert round(tea, 6) == 0.195618

    def test_18pct_annual(self):
        """18% nominal cap. anual → TEA = 18% (identidad)."""
        tea = nominal_to_effective(0.18, "annual")
        assert tea == 0.18

    def test_18pct_semiannual(self):
        """18% nominal cap. semestral → TEA = 18.81%."""
        tea = nominal_to_effective(0.18, "semiannual")
        assert round(tea, 4) == 0.1881

    def test_continuous_compounding(self):
        """12% nominal cap. continua → TEA = e^0.12 - 1 ≈ 12.75%."""
        tea = nominal_to_effective(0.12, "continuous")
        expected = math.exp(0.12) - 1
        assert abs(tea - expected) < 1e-10

    def test_zero_rate(self):
        """0% nominal → TEA = 0%."""
        tea = nominal_to_effective(0.0, "monthly")
        assert tea == 0.0

    def test_numeric_periods(self):
        """Acepta períodos como entero directo."""
        tea = nominal_to_effective(0.18, 4)  # 4 = trimestral
        assert round(tea, 6) == 0.192519

    def test_daily_compounding(self):
        """Capitalización diaria produce mayor TEA que mensual."""
        tea_daily = nominal_to_effective(0.12, "daily")
        tea_monthly = nominal_to_effective(0.12, "monthly")
        assert tea_daily > tea_monthly

    def test_higher_frequency_higher_tea(self):
        """A mayor frecuencia de capitalización, mayor TEA (con tasa positiva)."""
        tea_annual = nominal_to_effective(0.10, "annual")
        tea_semi = nominal_to_effective(0.10, "semiannual")
        tea_quarterly = nominal_to_effective(0.10, "quarterly")
        tea_monthly = nominal_to_effective(0.10, "monthly")

        assert tea_annual < tea_semi < tea_quarterly < tea_monthly

    def test_rejects_extreme_rate(self):
        """Rechaza tasas absurdas (>1000%)."""
        with pytest.raises(ValueError, match="excede el máximo"):
            nominal_to_effective(15.0, "annual")

    def test_rejects_invalid_compounding(self):
        """Rechaza período de capitalización no reconocido."""
        with pytest.raises(ValueError, match="no reconocido"):
            nominal_to_effective(0.12, "hourly")

    def test_rejects_nan(self):
        """Rechaza NaN."""
        with pytest.raises(ValueError, match="finito"):
            nominal_to_effective(float("nan"), "monthly")


# ---------------------------------------------------------------------------
# effective_to_nominal (inversa)
# ---------------------------------------------------------------------------


class TestEffectiveToNominal:
    """Tests de conversión inversa TEA → nominal."""

    def test_roundtrip_quarterly(self):
        """TEA → nominal → TEA debe ser idempotente."""
        original_nominal = 0.18
        tea = nominal_to_effective(original_nominal, "quarterly")
        recovered = effective_to_nominal(tea, "quarterly")
        assert abs(recovered - original_nominal) < 1e-8

    def test_roundtrip_monthly(self):
        """Roundtrip mensual."""
        tea = nominal_to_effective(0.24, "monthly")
        recovered = effective_to_nominal(tea, "monthly")
        assert abs(recovered - 0.24) < 1e-8

    def test_roundtrip_continuous(self):
        """Roundtrip capitalización continua."""
        tea = nominal_to_effective(0.10, "continuous")
        recovered = effective_to_nominal(tea, "continuous")
        assert abs(recovered - 0.10) < 1e-10


# ---------------------------------------------------------------------------
# effective_to_periodic / periodic_to_effective
# ---------------------------------------------------------------------------


class TestPeriodicConversions:
    """Tests de tasa periódica."""

    def test_tea_to_monthly(self):
        """TEA 12% → tasa mensual NO es 1%."""
        monthly = effective_to_periodic(0.12, 12)
        # (1.12)^(1/12) - 1 ≈ 0.9489%
        assert round(monthly * 100, 2) == 0.95

    def test_periodic_roundtrip(self):
        """Roundtrip periódica → TEA → periódica."""
        periodic = 0.015  # 1.5% mensual
        tea = periodic_to_effective(periodic, 12)
        recovered = effective_to_periodic(tea, 12)
        assert abs(recovered - periodic) < 1e-10

    def test_rejects_zero_periods(self):
        """Rechaza 0 períodos por año."""
        with pytest.raises(ValueError):
            effective_to_periodic(0.12, 0)


# ---------------------------------------------------------------------------
# Fisher — Tasa Real
# ---------------------------------------------------------------------------


class TestFisherEquation:
    """Tests de la ecuación de Fisher."""

    def test_nominal_15_inflation_5(self):
        """Nominal 15%, inflación 5% → real ≈ 9.52%."""
        r = real_rate(0.15, 0.05)
        assert round(r, 4) == 0.0952

    def test_nominal_equals_inflation(self):
        """Si nominal = inflación → real ≈ 0%."""
        r = real_rate(0.05, 0.05)
        assert abs(r) < 1e-10

    def test_negative_real_rate(self):
        """Si inflación > nominal → tasa real negativa."""
        r = real_rate(0.03, 0.08)
        assert r < 0

    def test_fisher_inverse(self):
        """Fisher inverso: real + inflación → nominal."""
        r_real = 0.08
        inflation = 0.05
        nominal = nominal_rate_from_real(r_real, inflation)
        # (1.08)(1.05) - 1 = 0.134
        assert round(nominal, 3) == 0.134

    def test_fisher_roundtrip(self):
        """nominal → real → nominal debe ser consistente."""
        nom = 0.15
        inf = 0.05
        r = real_rate(nom, inf)
        recovered = nominal_rate_from_real(r, inf)
        assert abs(recovered - nom) < 1e-10


# ---------------------------------------------------------------------------
# Comparación de Tasas
# ---------------------------------------------------------------------------


class TestCompareRates:
    """Tests de comparación de múltiples tasas."""

    def test_same_nominal_different_compounding(self):
        """18% nominal con diferente capitalización → TEA diferentes."""
        result = compare_rates(
            [
                {"label": "Banco A", "nominal_rate": 0.18, "compounding": "annual"},
                {"label": "Banco B", "nominal_rate": 0.18, "compounding": "quarterly"},
                {"label": "Banco C", "nominal_rate": 0.18, "compounding": "monthly"},
            ],
            perspective="borrower",
        )
        # Para deudor, Banco A (anual) debe ser rank 1 (menor TEA)
        assert result.items[0].label == "Banco A"
        assert result.items[-1].label == "Banco C"
        assert result.cheapest_label == "Banco A"
        assert result.spread_bps > 0

    def test_investor_perspective(self):
        """Perspectiva inversor: mayor TEA = mejor."""
        result = compare_rates(
            [
                {"label": "Fondo A", "nominal_rate": 0.12, "compounding": "annual"},
                {"label": "Fondo B", "nominal_rate": 0.12, "compounding": "monthly"},
            ],
            perspective="investor",
        )
        # Inversor quiere mayor TEA → mensual (rank 1)
        assert result.items[0].label == "Fondo B"

    def test_empty_list_raises(self):
        """Lista vacía debe lanzar error."""
        with pytest.raises(ValueError):
            compare_rates([], "borrower")


# ---------------------------------------------------------------------------
# WACC
# ---------------------------------------------------------------------------


class TestWACC:
    """Tests del WACC."""

    def test_basic_wacc(self):
        """WACC con equity=$600k, debt=$400k, Ke=12%, Kd=8%, T=30%."""
        result = wacc(
            equity=600_000,
            debt=400_000,
            cost_of_equity=0.12,
            cost_of_debt=0.08,
            tax_rate=0.30,
        )
        # 0.6*0.12 + 0.4*0.08*0.7 = 0.072 + 0.0224 = 0.0944
        assert round(result, 4) == 0.0944

    def test_all_equity(self):
        """100% equity → WACC = Ke."""
        result = wacc(
            equity=1_000_000, debt=0, cost_of_equity=0.15,
            cost_of_debt=0.10, tax_rate=0.30,
        )
        assert round(result, 4) == 0.15

    def test_rejects_zero_total(self):
        """Equity + Debt = 0 → error."""
        with pytest.raises(ValueError):
            wacc(0, 0, 0.12, 0.08, 0.30)
