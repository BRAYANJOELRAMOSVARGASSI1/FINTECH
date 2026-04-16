"""
test_amortization.py — Tests para tablas de amortización.
"""

import pytest

from app.core.amortization import (
    american_amortization,
    compare_amortization_systems,
    french_amortization,
    german_amortization,
)


class TestFrenchAmortization:
    """Tests del Sistema Francés."""

    def test_fixed_payment(self):
        """Todas las cuotas deben ser (casi) iguales."""
        table = french_amortization(100_000, 0.12, 12, 12)
        payments = table.payments
        # Permitir $0.02 de diferencia por redondeo en la última cuota
        for p in payments[:-1]:
            assert abs(p - payments[0]) < 0.02

    def test_balance_zero_at_end(self):
        """Saldo final debe ser 0."""
        table = french_amortization(100_000, 0.12, 12, 12)
        assert table.rows[-1].balance == 0.0

    def test_total_principal_equals_loan(self):
        """Total amortizado ≈ principal original."""
        table = french_amortization(50_000, 0.10, 24, 12)
        assert abs(table.total_principal - 50_000) < 1.0

    def test_interest_decreases(self):
        """Intereses deben ser decrecientes en Francés."""
        table = french_amortization(100_000, 0.12, 12, 12)
        interests = [row.interest for row in table.rows]
        assert all(interests[i] >= interests[i + 1] for i in range(len(interests) - 1))

    def test_zero_rate(self):
        """Tasa 0% → cuota = principal / períodos."""
        table = french_amortization(12_000, 0.0, 12, 12)
        assert abs(table.payments[0] - 1_000) < 0.01


class TestGermanAmortization:
    """Tests del Sistema Alemán."""

    def test_fixed_principal(self):
        """Amortización de capital debe ser constante."""
        table = german_amortization(100_000, 0.12, 10, 12)
        principals = [row.principal for row in table.rows[:-1]]  # Excluir última (ajuste)
        for p in principals:
            assert abs(p - principals[0]) < 1.0

    def test_decreasing_payments(self):
        """Cuotas deben ser decrecientes."""
        table = german_amortization(100_000, 0.12, 12, 12)
        payments = table.payments
        assert all(payments[i] >= payments[i + 1] for i in range(len(payments) - 1))

    def test_balance_zero(self):
        """Saldo final = 0."""
        table = german_amortization(100_000, 0.12, 24, 12)
        assert table.rows[-1].balance == 0.0


class TestAmericanAmortization:
    """Tests del Sistema Americano."""

    def test_only_interest_until_last(self):
        """Solo intereses hasta la última cuota."""
        table = american_amortization(100_000, 0.12, 12, 12)
        for row in table.rows[:-1]:
            assert row.principal == 0.0
            assert row.balance == 100_000.0

    def test_bullet_payment(self):
        """Última cuota incluye el capital completo."""
        table = american_amortization(100_000, 0.12, 12, 12)
        assert table.rows[-1].principal == 100_000.0
        assert table.rows[-1].balance == 0.0

    def test_most_expensive(self):
        """Americano paga más intereses que Francés y Alemán."""
        tables = compare_amortization_systems(100_000, 0.12, 24, 12)
        assert tables["american"].total_interest > tables["french"].total_interest
        assert tables["american"].total_interest > tables["german"].total_interest


class TestCompareAmortization:
    """Tests de comparación de sistemas."""

    def test_german_cheapest(self):
        """Alemán siempre paga menos intereses que Francés."""
        tables = compare_amortization_systems(100_000, 0.12, 24, 12)
        assert tables["german"].total_interest < tables["french"].total_interest

    def test_all_same_principal(self):
        """Los tres sistemas amortizan el mismo principal."""
        tables = compare_amortization_systems(100_000, 0.12, 12, 12)
        for system in ["french", "german", "american"]:
            assert abs(tables[system].total_principal - 100_000) < 1.0

    def test_summary_works(self):
        """El método summary() retorna diccionario válido."""
        tables = compare_amortization_systems(50_000, 0.08, 12, 12)
        for table in tables.values():
            s = table.summary()
            assert "total_paid" in s
            assert "total_interest" in s
            assert s["total_paid"] > 0
