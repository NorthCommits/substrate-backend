import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.context import Context, ContextStatus
from app.schemas.context import ContextPublish, ContextStatusUpdate
from app.services.agent_service import get_agent_by_id
from app.services.embedding_service import generate_embedding, find_similar_contexts
from app.services.lineage_service import record_lineage
from app.utils.exceptions import ContextNotFoundException


async def publish_context(
    db: AsyncSession,
    data: ContextPublish
) -> Context:
    await get_agent_by_id(db, data.producer_id)

    embedding = await generate_embedding(
        f"{data.key} {data.context_type} {str(data.value)}"
    )

    context = Context(
        id=uuid.uuid4(),
        key=data.key,
        value=data.value,
        context_type=data.context_type,
        status=ContextStatus.active,
        embedding=embedding,
        producer_id=data.producer_id,
    )
    db.add(context)
    await db.flush()

    await record_lineage(
        db=db,
        context_id=context.id,
        agent_id=data.producer_id,
        action="published",
        snapshot=data.value,
        note=f"Context '{data.key}' published by agent"
    )

    await db.refresh(context, ["producer"])
    return context


async def get_context_by_id(
    db: AsyncSession,
    context_id: uuid.UUID
) -> Context:
    result = await db.execute(
        select(Context)
        .where(Context.id == context_id)
        .options(selectinload(Context.producer))
    )
    context = result.scalar_one_or_none()
    if not context:
        raise ContextNotFoundException(str(context_id))
    return context


async def get_all_contexts(
    db: AsyncSession,
    context_type: str | None = None,
    status: ContextStatus | None = None,
    producer_id: uuid.UUID | None = None,
) -> list[Context]:
    query = select(Context).options(selectinload(Context.producer))

    if context_type:
        query = query.where(Context.context_type == context_type)
    if status:
        query = query.where(Context.status == status)
    if producer_id:
        query = query.where(Context.producer_id == producer_id)

    query = query.order_by(Context.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_context_status(
    db: AsyncSession,
    context_id: uuid.UUID,
    agent_id: uuid.UUID,
    data: ContextStatusUpdate
) -> Context:
    context = await get_context_by_id(db, context_id)
    previous_status = context.status
    context.status = data.status
    await db.flush()

    await record_lineage(
        db=db,
        context_id=context.id,
        agent_id=agent_id,
        action=f"marked_{data.status.value}",
        snapshot=context.value,
        note=f"Status changed from '{previous_status}' to '{data.status.value}'"
    )

    await db.refresh(context, ["producer"])
    return context


async def search_similar_contexts(
    db: AsyncSession,
    query: str,
    threshold: float = 0.75,
    top_k: int = 5
) -> list[Context]:
    result = await db.execute(
        select(Context)
        .where(Context.embedding.isnot(None))
        .options(selectinload(Context.producer))
    )
    all_contexts = list(result.scalars().all())

    stored_embeddings = [
        (str(c.id), c.embedding)
        for c in all_contexts
        if c.embedding
    ]

    similar_ids = await find_similar_contexts(
        query=query,
        stored_embeddings=stored_embeddings,
        threshold=threshold,
        top_k=top_k
    )

    id_to_context = {str(c.id): c for c in all_contexts}
    return [id_to_context[cid] for cid in similar_ids if cid in id_to_context]