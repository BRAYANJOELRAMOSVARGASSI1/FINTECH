"""
test_taxes.py — Tests para depreciación y escudos fiscales.
"""

import pytest

from app.core.taxes import (
    after_tax_cost,
    asset_disposal,
    declining_balance_depreciation,
    straight_line_depreciation,
    sum_of_years_digits_depreciation,
    tax_shield,
)


class TestStraightLineDepreciation:
    """Tests de depreciación lineal."""

    def test_basic(self):
        """$100k activo, $10k salvamento, 5 años → $18k/año."""
        result = straight_line_depreciation(100_000, 10_000, 5, 0.30)
        assert len(result.annual_depreciation) == 5
        assert all(d == 18_000.0 for d in result.annual_depreciation)
        assert result.total_depreciation == 90_000.0

    def test_tax_shield(self):
        """Escudo fiscal = depreciación × tasa."""
        result = straight_line_depreciation(100_000, 10_000, 5, 0.30)
        assert all(s == 5_400.0 for s in result.annual_tax_shield)
        assert result.total_tax_shield == 27_000.0

    def test_book_value_decreases(self):
        """Valor en libros debe decrecer cada año."""
        result = straight_line_depreciation(50_000, 5_000, 5)
        book_values = [row.book_value for row in result.rows]
        assert all(book_values[i] > book_values[i + 1] for i in range(len(book_values) - 1))
        assert result.rows[-1].book_value == 5_000.0

    def test_rejects_salvage_gte_cost(self):
        """Salvamento >= costo → error."""
        with pytest.raises(ValueError):
            straight_line_depreciation(100_000, 100_000, 5)


class TestDecliningBalance:
    """Tests de depreciación acelerada DDB."""

    def test_front_loaded(self):
        """DDB produce mayor depreciación en años iniciales."""
        result = declining_balance_depreciation(100_000, 10_000, 5, 0.30)
        deps = result.annual_depreciation
        assert deps[0] > deps[-1]  # Primero > último

    def test_never_below_salvage(self):
        """Valor en libros nunca cae debajo del salvamento."""
        result = declining_balance_depreciation(100_000, 10_000, 5)
        for row in result.rows:
            assert row.book_value >= 10_000.0 - 0.01  # Tolerancia redondeo


class TestSYD:
    """Tests de suma de dígitos."""

    def test_syd_total(self):
        """Total depreciado = costo - salvamento."""
        result = sum_of_years_digits_depreciation(100_000, 10_000, 5)
        assert abs(result.total_depreciation - 90_000.0) < 0.01

    def test_syd_decreasing(self):
        """SYD debe ser decreciente."""
        result = sum_of_years_digits_depreciation(50_000, 5_000, 5)
        deps = result.annual_depreciation
        assert all(deps[i] >= deps[i + 1] for i in range(len(deps) - 1))


class TestTaxShield:
    """Tests del escudo fiscal."""

    def test_basic_shield(self):
        """Shield = dep × tax."""
        shields = tax_shield([10_000, 10_000, 10_000], 0.30)
        assert shields == [3_000.0, 3_000.0, 3_000.0]

    def test_zero_tax(self):
        """Sin impuestos → sin escudo."""
        shields = tax_shield([10_000, 10_000], 0.0)
        assert shields == [0.0, 0.0]


class TestAfterTaxCost:
    """Tests de costo después de impuestos."""

    def test_basic(self):
        """$10k gasto con 30% tax → $7k costo real."""
        assert after_tax_cost(10_000, 0.30) == 7_000.0

    def test_zero_tax(self):
        """Sin impuestos → costo completo."""
        assert after_tax_cost(10_000, 0.0) == 10_000.0


class TestAssetDisposal:
    """Tests de disposición de activos."""

    def test_gain_on_sale(self):
        """Venta por encima del valor en libros → ganancia gravable."""
        result = asset_disposal(100_000, 80_000, 25_000, 0.30)
        assert result.book_value_at_sale == 20_000.0
        assert result.gain_or_loss == 5_000.0
        assert result.is_gain is True
        assert result.tax_on_gain == 1_500.0
        assert result.net_proceeds == 23_500.0

    def test_loss_on_sale(self):
        """Venta por debajo del valor en libros → pérdida deducible."""
        result = asset_disposal(100_000, 60_000, 30_000, 0.30)
        assert result.book_value_at_sale == 40_000.0
        assert result.gain_or_loss == -10_000.0
        assert result.is_gain is False
        # Tax benefit: -10k * 0.30 = -3k → net proceeds = 30k + 3k = 33k
        assert result.net_proceeds == 33_000.0
