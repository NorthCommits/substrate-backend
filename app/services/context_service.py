import uuid

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.context import Context, ContextStatus, ContextVisibility
from app.schemas.context import ContextPublish, ContextStatusUpdate, ContextVisibilityUpdate
from app.services.agent_service import get_agent_by_id
from app.services.embedding_service import generate_embedding, find_similar_contexts
from app.services.lineage_service import record_lineage
from app.utils.exceptions import ContextNotFoundException, ContextForbiddenException


async def publish_context(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    agent_id: uuid.UUID,
    data: ContextPublish
) -> Context:
    agent = await get_agent_by_id(db, agent_id, workspace_id)

    embedding = await generate_embedding(
        f"{data.key} {data.context_type} {str(data.value)}"
    )

    context = Context(
        id=uuid.uuid4(),
        key=data.key,
        value=data.value,
        context_type=data.context_type,
        status=ContextStatus.active,
        visibility=data.visibility,
        embedding=embedding,
        producer_id=agent_id,
        workspace_id=workspace_id,
    )
    db.add(context)
    await db.flush()

    await record_lineage(
        db=db,
        context_id=context.id,
        agent_id=agent_id,
        action="published",
        snapshot=data.value,
        note=f"Context '{data.key}' published by agent '{agent.name}'"
    )

    await db.refresh(context, ["producer"])
    return context


async def get_context_by_id(
    db: AsyncSession,
    context_id: uuid.UUID,
    workspace_id: uuid.UUID | None = None
) -> Context:
    result = await db.execute(
        select(Context)
        .where(Context.id == context_id)
        .options(selectinload(Context.producer))
    )
    context = result.scalar_one_or_none()
    if not context:
        raise ContextNotFoundException(str(context_id))

    if workspace_id:
        is_own = context.workspace_id == workspace_id
        is_public = context.visibility == ContextVisibility.public
        if not is_own and not is_public:
            raise ContextForbiddenException()

    return context


async def get_workspace_contexts(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    context_type: str | None = None,
    status: ContextStatus | None = None,
) -> list[Context]:
    query = select(Context).options(selectinload(Context.producer))
    query = query.where(Context.workspace_id == workspace_id)

    if context_type:
        query = query.where(Context.context_type == context_type)
    if status:
        query = query.where(Context.status == status)

    query = query.order_by(Context.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_public_contexts(
    db: AsyncSession,
    context_type: str | None = None,
    status: ContextStatus | None = None,
) -> list[Context]:
    query = select(Context).options(selectinload(Context.producer))
    query = query.where(Context.visibility == ContextVisibility.public)

    if context_type:
        query = query.where(Context.context_type == context_type)
    if status:
        query = query.where(Context.status == status)

    query = query.order_by(Context.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_context_status(
    db: AsyncSession,
    context_id: uuid.UUID,
    agent_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: ContextStatusUpdate
) -> Context:
    context = await get_context_by_id(db, context_id, workspace_id)
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


async def update_context_visibility(
    db: AsyncSession,
    context_id: uuid.UUID,
    agent_id: uuid.UUID,
    workspace_id: uuid.UUID,
    data: ContextVisibilityUpdate
) -> Context:
    context = await get_context_by_id(db, context_id, workspace_id)
    previous_visibility = context.visibility
    context.visibility = data.visibility
    await db.flush()

    await record_lineage(
        db=db,
        context_id=context.id,
        agent_id=agent_id,
        action=f"visibility_changed",
        snapshot=context.value,
        note=f"Visibility changed from '{previous_visibility}' to '{data.visibility.value}'"
    )

    await db.refresh(context, ["producer"])
    return context


async def search_similar_contexts(
    db: AsyncSession,
    query: str,
    workspace_id: uuid.UUID | None = None,
    threshold: float = 0.75,
    top_k: int = 5
) -> list[Context]:
    q = select(Context).options(selectinload(Context.producer))

    if workspace_id:
        q = q.where(
            or_(
                Context.workspace_id == workspace_id,
                Context.visibility == ContextVisibility.public
            )
        )
    else:
        q = q.where(Context.visibility == ContextVisibility.public)

    q = q.where(Context.embedding.isnot(None))
    result = await db.execute(q)
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