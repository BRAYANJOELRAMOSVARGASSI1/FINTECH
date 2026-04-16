"""
amortization.py — Tablas de Amortización de Deuda.

Implementa los tres sistemas de amortización más usados en
la banca y finanzas corporativas:

1. Sistema Francés (Cuota Fija):
   - La cuota total es CONSTANTE cada período.
   - La proporción de interés DECRECE y la amortización CRECE.
   - Es el más común en créditos hipotecarios y personales.
   - Fórmula: Cuota = P × [r(1+r)^n] / [(1+r)^n - 1]

2. Sistema Alemán (Amortización Constante):
   - La amortización de capital es CONSTANTE.
   - La cuota total DECRECE porque los intereses bajan.
   - Paga menos intereses totales que el Francés.
   - Fórmula: Amort = P / n, Cuota_t = Amort + Saldo_t × r

3. Sistema Americano (Bullet):
   - Solo paga INTERESES durante la vida del préstamo.
   - El capital completo se devuelve al FINAL (bullet payment).
   - Mayor riesgo para el prestamista, mayor gasto total de intereses.

References:
    - Hull, J. — Options, Futures, and Other Derivatives
    - Brealey & Myers — Principles of Corporate Finance
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy_financial as npf


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AmortizationRow:
    """Fila individual de una tabla de amortización."""

    period: int
    payment: float  # Cuota total
    interest: float  # Porción de interés
    principal: float  # Porción de amortización del capital
    balance: float  # Saldo pendiente después del pago


@dataclass(frozen=True, slots=True)
class AmortizationTable:
    """Tabla completa de amortización de un préstamo."""

    system: str  # "french", "german", "american"
    principal: float
    annual_rate: float
    periodic_rate: float
    total_periods: int
    periods_per_year: int
    rows: list[AmortizationRow] = field(default_factory=list)

    @property
    def total_paid(self) -> float:
        """Total pagado durante la vida del préstamo."""
        return round(sum(row.payment for row in self.rows), 2)

    @property
    def total_interest(self) -> float:
        """Total de intereses pagados."""
        return round(sum(row.interest for row in self.rows), 2)

    @property
    def total_principal(self) -> float:
        """Total de capital amortizado (debe ≈ principal original)."""
        return round(sum(row.principal for row in self.rows), 2)

    @property
    def payments(self) -> list[float]:
        """Lista de cuotas totales por período."""
        return [row.payment for row in self.rows]

    @property
    def interest_ratio(self) -> float:
        """Ratio interés/capital (cuánto extra pagas por el préstamo)."""
        if self.principal == 0:
            return 0.0
        return round(self.total_interest / self.principal, 4)

    def summary(self) -> dict:
        """Resumen ejecutivo de la amortización."""
        return {
            "system": self.system,
            "principal": self.principal,
            "annual_rate_pct": round(self.annual_rate * 100, 4),
            "total_periods": self.total_periods,
            "total_paid": self.total_paid,
            "total_interest": self.total_interest,
            "interest_ratio": self.interest_ratio,
            "first_payment": self.rows[0].payment if self.rows else 0,
            "last_payment": self.rows[-1].payment if self.rows else 0,
        }


# ---------------------------------------------------------------------------
# Validación
# ---------------------------------------------------------------------------


def _validate_loan_params(
    principal: float, annual_rate: float, total_periods: int
) -> None:
    """Valida los parámetros del préstamo."""
    if principal <= 0:
        raise ValueError(f"El principal debe ser > 0, recibido: {principal}")
    if annual_rate < 0:
        raise ValueError(f"La tasa anual debe ser >= 0, recibido: {annual_rate}")
    if not math.isfinite(annual_rate):
        raise ValueError(f"La tasa anual debe ser finita, recibido: {annual_rate}")
    if total_periods < 1:
        raise ValueError(f"Total de períodos debe ser >= 1, recibido: {total_periods}")


# ---------------------------------------------------------------------------
# Sistema Francés — Cuota Fija
# ---------------------------------------------------------------------------


def french_amortization(
    principal: float,
    annual_rate: float,
    total_periods: int,
    periods_per_year: int = 12,
) -> AmortizationTable:
    """Genera tabla de amortización con Sistema Francés (cuota fija).

    Fórmula de la cuota:
        PMT = P × [r(1+r)^n] / [(1+r)^n - 1]

    Donde:
        P = Principal
        r = Tasa periódica
        n = Número total de períodos

    Args:
        principal: Monto del préstamo.
        annual_rate: Tasa de interés anual (TEA o nominal, según contexto).
        total_periods: Número total de cuotas.
        periods_per_year: Períodos por año (12=mensual, 4=trimestral, etc.).

    Returns:
        AmortizationTable completa.

    Examples:
        >>> table = french_amortization(100000, 0.12, 12, 12)
        >>> table.rows[0].payment  # Cuota fija mensual
        8884.88  # Aproximadamente
    """
    _validate_loan_params(principal, annual_rate, total_periods)

    # Tasa periódica
    periodic_rate = annual_rate / periods_per_year

    if periodic_rate == 0:
        # Sin interés — cuota = principal / períodos
        fixed_payment = principal / total_periods
        rows = []
        balance = principal
        for period in range(1, total_periods + 1):
            payment = round(fixed_payment, 2)
            if period == total_periods:
                payment = round(balance, 2)  # Ajuste por redondeo
            balance -= payment
            rows.append(
                AmortizationRow(
                    period=period,
                    payment=payment,
                    interest=0.0,
                    principal=payment,
                    balance=round(max(balance, 0), 2),
                )
            )
        return AmortizationTable(
            system="french",
            principal=principal,
            annual_rate=annual_rate,
            periodic_rate=0.0,
            total_periods=total_periods,
            periods_per_year=periods_per_year,
            rows=rows,
        )

    # Cuota fija usando numpy-financial
    fixed_payment = -float(npf.pmt(periodic_rate, total_periods, principal))

    rows = []
    balance = principal

    for period in range(1, total_periods + 1):
        interest = round(balance * periodic_rate, 2)
        principal_payment = round(fixed_payment - interest, 2)

        # Ajuste en la última cuota para cerrar exactamente
        if period == total_periods:
            principal_payment = round(balance, 2)
            fixed_payment_adj = interest + principal_payment
        else:
            fixed_payment_adj = fixed_payment

        balance -= principal_payment
        balance = max(balance, 0)  # Protección contra negativos por redondeo

        rows.append(
            AmortizationRow(
                period=period,
                payment=round(fixed_payment_adj, 2),
                interest=interest,
                principal=principal_payment,
                balance=round(balance, 2),
            )
        )

    return AmortizationTable(
        system="french",
        principal=principal,
        annual_rate=annual_rate,
        periodic_rate=round(periodic_rate, 8),
        total_periods=total_periods,
        periods_per_year=periods_per_year,
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Sistema Alemán — Amortización Constante
# ---------------------------------------------------------------------------


def german_amortization(
    principal: float,
    annual_rate: float,
    total_periods: int,
    periods_per_year: int = 12,
) -> AmortizationTable:
    """Genera tabla de amortización con Sistema Alemán (amortización constante).

    La amortización de capital es FIJA cada período:
        Amort = P / n

    La cuota total DECRECE porque los intereses bajan:
        Cuota_t = Amort + Saldo_(t-1) × r

    Ventaja: Paga MENOS intereses totales que el Sistema Francés.
    Desventaja: Las primeras cuotas son más altas.

    Args:
        principal: Monto del préstamo.
        annual_rate: Tasa de interés anual.
        total_periods: Número total de cuotas.
        periods_per_year: Períodos por año.

    Returns:
        AmortizationTable completa.
    """
    _validate_loan_params(principal, annual_rate, total_periods)

    periodic_rate = annual_rate / periods_per_year
    fixed_amortization = principal / total_periods

    rows = []
    balance = principal

    for period in range(1, total_periods + 1):
        interest = round(balance * periodic_rate, 2)
        amort = round(fixed_amortization, 2)

        # Ajuste en la última cuota
        if period == total_periods:
            amort = round(balance, 2)

        payment = round(amort + interest, 2)
        balance -= amort
        balance = max(balance, 0)

        rows.append(
            AmortizationRow(
                period=period,
                payment=payment,
                interest=interest,
                principal=amort,
                balance=round(balance, 2),
            )
        )

    return AmortizationTable(
        system="german",
        principal=principal,
        annual_rate=annual_rate,
        periodic_rate=round(periodic_rate, 8),
        total_periods=total_periods,
        periods_per_year=periods_per_year,
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Sistema Americano — Bullet Payment
# ---------------------------------------------------------------------------


def american_amortization(
    principal: float,
    annual_rate: float,
    total_periods: int,
    periods_per_year: int = 12,
) -> AmortizationTable:
    """Genera tabla de amortización con Sistema Americano (bullet).

    Solo se pagan INTERESES durante la vida del préstamo.
    El capital COMPLETO se devuelve en el último período.

    Cuota_1...(n-1) = Saldo × r  (solo intereses)
    Cuota_n = Saldo × r + P      (intereses + capital completo)

    Es el sistema más CARO en intereses totales, pero alivia
    el flujo de caja durante la vida del préstamo.

    Args:
        principal: Monto del préstamo.
        annual_rate: Tasa de interés anual.
        total_periods: Número total de períodos.
        periods_per_year: Períodos por año.

    Returns:
        AmortizationTable completa.
    """
    _validate_loan_params(principal, annual_rate, total_periods)

    periodic_rate = annual_rate / periods_per_year
    interest_payment = round(principal * periodic_rate, 2)

    rows = []

    for period in range(1, total_periods + 1):
        if period < total_periods:
            rows.append(
                AmortizationRow(
                    period=period,
                    payment=interest_payment,
                    interest=interest_payment,
                    principal=0.0,
                    balance=round(principal, 2),
                )
            )
        else:
            # Último período: interés + capital completo
            final_payment = interest_payment + principal
            rows.append(
                AmortizationRow(
                    period=period,
                    payment=round(final_payment, 2),
                    interest=interest_payment,
                    principal=round(principal, 2),
                    balance=0.0,
                )
            )

    return AmortizationTable(
        system="american",
        principal=principal,
        annual_rate=annual_rate,
        periodic_rate=round(periodic_rate, 8),
        total_periods=total_periods,
        periods_per_year=periods_per_year,
        rows=rows,
    )


# ---------------------------------------------------------------------------
# Comparación de Sistemas
# ---------------------------------------------------------------------------


def compare_amortization_systems(
    principal: float,
    annual_rate: float,
    total_periods: int,
    periods_per_year: int = 12,
) -> dict[str, AmortizationTable]:
    """Compara los tres sistemas de amortización para los mismos parámetros.

    Útil para que un CFO vea cuál sistema le conviene según
    su situación de flujo de caja.

    Returns:
        Diccionario con las tres tablas de amortización.
    """
    return {
        "french": french_amortization(principal, annual_rate, total_periods, periods_per_year),
        "german": german_amortization(principal, annual_rate, total_periods, periods_per_year),
        "american": american_amortization(principal, annual_rate, total_periods, periods_per_year),
    }

def revolving_credit_facility(
    annual_rate: float,
    drawdowns: list[float],
    payments: list[float],
    periods_per_year: int = 12,
) -> AmortizationTable:
    """Calcula la tabla de amortización para una Línea de Crédito Revolving.
    
    A diferencia de un préstamo tradicional (Francés/Alemán), una línea revolving:
    - No tiene un principal desembolsado el día 0 exclusivamente.
    - Se pueden hacer retiros (drawdowns) en cualquier período.
    - Se pueden hacer pagos variables.
    - El interés se calcula sobre el saldo vivo del período anterior.
    
    Args:
        annual_rate: Tasa de interés anual.
        drawdowns: Lista de montos retirados por período.
        payments: Lista de pagos realizados por período.
        periods_per_year: Periodos por año.
        
    Returns:
        AmortizationTable conteniendo el historial de la línea de crédito.
    """
    total_periods = max(len(drawdowns), len(payments))
    
    # Rellenar con ceros si las listas no son del mismo tamaño
    drawdowns = drawdowns + [0.0] * (total_periods - len(drawdowns))
    payments = payments + [0.0] * (total_periods - len(payments))
    
    _validate_loan_params(1.0, annual_rate, total_periods) # Validación genérica
    
    periodic_rate = annual_rate / periods_per_year
    rows = []
    balance = 0.0
    
    for period in range(1, total_periods + 1):
        idx = period - 1
        
        drawdown = drawdowns[idx]
        payment = payments[idx]
        
        # El interés se cobra sobre el saldo con el que se INICIA el período
        # más el drawdown del mismo período (simplificación financiera estándar)
        # Asumiendo retiros al inicio de mes y pagos al final.
        starting_balance = balance + drawdown
        interest = round(starting_balance * periodic_rate, 2)
        
        # El pago cubre primero los intereses, el resto va a capital
        if payment >= interest:
            principal_payment = round(payment - interest, 2)
            interest_paid = interest
        else:
            principal_payment = 0.0
            interest_paid = payment
            # El interés no pagado se capitaliza (añade al saldo)
            starting_balance += (interest - payment)
            
        # Actualizar saldo final
        balance = round(starting_balance - principal_payment, 2)
        balance = max(balance, 0.0) # No puede haber saldo negativo
        
        rows.append(
            AmortizationRow(
                period=period,
                payment=round(payment, 2),
                interest=round(interest_paid, 2),
                principal=round(principal_payment, 2),
                balance=balance,
            )
        )
        
    # Calcular un "principal base aproximado" para mantener la interfaz original
    max_debt = sum(drawdowns)
        
    return AmortizationTable(
        system="revolving",
        principal=round(max_debt, 2),
        annual_rate=annual_rate,
        periodic_rate=round(periodic_rate, 8),
        total_periods=total_periods,
        periods_per_year=periods_per_year,
        rows=rows,
    )
