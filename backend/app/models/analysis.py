"""
models/analysis.py -- Modelo de analisis financiero + series temporales.

Cada analisis almacena el tipo (capex_opex, rate_comparison, etc.),
los parametros de entrada como JSONB, y los resultados como JSONB.
CashFlowSeries almacena flujos de caja periodo a periodo.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Text, Float, Integer, DateTime, ForeignKey, JSON, Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Analysis(Base):
    """Analisis financiero individual (un calculo ejecutado)."""

    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    analysis_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # rate_comparison | npv_irr | amortization | capex_opex | montecarlo
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # JSONB: parametros de entrada del calculo
    input_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # JSONB: resultados completos del calculo
    results: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Metadata
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="completed"
    )  # pending | running | completed | failed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="analyses")  # noqa: F821
    cash_flow_series: Mapped[list["CashFlowSeries"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan"
    )

    # Indices
    __table_args__ = (
        Index("ix_analyses_project_type", "project_id", "analysis_type"),
        Index("ix_analyses_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Analysis {self.analysis_type} [{self.status}]>"


class CashFlowSeries(Base):
    """Serie temporal de flujos de caja asociada a un analisis."""

    __tablename__ = "cash_flow_series"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    analysis_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="net"
    )  # net | revenue | opex | capex | tax | depreciation
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    analysis: Mapped["Analysis"] = relationship(back_populates="cash_flow_series")

    # Indices
    __table_args__ = (
        Index("ix_cashflow_analysis_period", "analysis_id", "period"),
    )

    def __repr__(self) -> str:
        return f"<CashFlow P{self.period} {self.category}: {self.amount}>"
