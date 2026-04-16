"""
models/project.py -- Modelo de proyecto financiero.

Un proyecto agrupa multiples analisis (rate comparisons, CAPEX vs OPEX,
Monte Carlo, etc.) bajo un mismo contexto de negocio.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Project(Base):
    """Proyecto financiero que contiene multiples analisis."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    company_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="draft"
    )  # draft | active | archived

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="projects")  # noqa: F821
    created_by_user: Mapped["User | None"] = relationship(  # noqa: F821
        back_populates="projects"
    )
    analyses: Mapped[list["Analysis"]] = relationship(  # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )

    # Indices
    __table_args__ = (
        Index("ix_projects_company_status", "company_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Project {self.name} [{self.status}]>"
