"""
models/audit.py -- Audit trail para compliance y trazabilidad.

Registra cada accion importante: creacion de proyectos, ejecucion
de analisis, cambios de rol, etc. Inmutable por diseno.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuditLog(Base):
    """Registro de auditoria inmutable."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # create | update | delete | login | export | analysis_run
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # user | project | analysis | company
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Detalles del cambio
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # IP y user agent para seguridad
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    user: Mapped["User | None"] = relationship(back_populates="audit_logs")  # noqa: F821

    # Indices
    __table_args__ = (
        Index("ix_audit_user_action", "user_id", "action"),
        Index("ix_audit_entity", "entity_type", "entity_id"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity_type}:{self.entity_id}>"
