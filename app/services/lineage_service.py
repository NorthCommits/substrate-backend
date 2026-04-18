import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lineage import Lineage


async def record_lineage(
    db: AsyncSession,
    context_id: uuid.UUID,
    agent_id: uuid.UUID,
    action: str,
    snapshot: dict | None = None,
    note: str | None = None
) -> Lineage:
    lineage = Lineage(
        id=uuid.uuid4(),
        context_id=context_id,
        agent_id=agent_id,
        action=action,
        snapshot=snapshot,
        note=note
    )
    db.add(lineage)
    await db.flush()
    return lineage


async def get_context_lineage(
    db: AsyncSession,
    context_id: uuid.UUID
) -> list[Lineage]:
    result = await db.execute(
        select(Lineage)
        .where(Lineage.context_id == context_id)
        .options(selectinload(Lineage.agent))
        .order_by(Lineage.created_at.asc())
    )
    return list(result.scalars().all())