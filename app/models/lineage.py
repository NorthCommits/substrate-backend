import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Lineage(Base):
    __tablename__ = "lineages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    context_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contexts.id"),
        nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=False
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSON, nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    context: Mapped["Context"] = relationship(
        "Context",
        back_populates="lineages"
    )
    agent: Mapped["Agent"] = relationship(
        "Agent",
        foreign_keys=[agent_id]
    )