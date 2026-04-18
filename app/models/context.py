import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class ContextStatus(str, Enum):
    active = "active"
    stale = "stale"
    conflicting = "conflicting"


class Context(Base):
    __tablename__ = "contexts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    context_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[ContextStatus] = mapped_column(
        String(50),
        default=ContextStatus.active,
        nullable=False
    )
    embedding: Mapped[list] = mapped_column(JSON, nullable=True)
    producer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    producer: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="published_contexts",
        foreign_keys=[producer_id]
    )
    lineages: Mapped[list["Lineage"]] = relationship(
        "Lineage",
        back_populates="context"
    )