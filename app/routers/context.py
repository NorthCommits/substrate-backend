import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis
from app.middleware.api_key_auth import get_workspace_from_api_key, get_api_key_record
from app.models.context import ContextStatus
from app.models.workspace import Workspace
from app.models.api_key import ApiKey
from app.schemas.context import (
    ContextPublish,
    ContextStatusUpdate,
    ContextVisibilityUpdate,
    ContextResponse,
    ContextSummary
)
from app.schemas.lineage import LineageResponse
from app.services import context_service, lineage_service, redis_service
from app.services.subscription_service import get_subscribers_for_context_type


router = APIRouter(prefix="/context", tags=["Context"])


@router.post("/publish", response_model=ContextResponse, status_code=201)
async def publish_context(
    data: ContextPublish,
    agent_id: uuid.UUID = Query(...),
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    context = await context_service.publish_context(
        db=db,
        workspace_id=workspace.id,
        agent_id=agent_id,
        data=data
    )

    subscribers = await get_subscribers_for_context_type(
        db=db,
        context_type=context.context_type,
        producer_id=context.producer_id
    )

    await redis_service.publish_context_event(
        redis=redis,
        context_type=context.context_type,
        workspace_id=str(workspace.id),
        payload={
            "context_id": str(context.id),
            "key": context.key,
            "context_type": context.context_type,
            "producer_id": str(context.producer_id),
            "visibility": context.visibility.value,
            "subscribers": [str(s.agent_id) for s in subscribers]
        }
    )

    if context.visibility.value == "public":
        await redis_service.publish_public_context_event(
            redis=redis,
            context_type=context.context_type,
            payload={
                "context_id": str(context.id),
                "key": context.key,
                "context_type": context.context_type,
                "producer_id": str(context.producer_id),
                "workspace_id": str(workspace.id),
            }
        )

    await redis_service.cache_context(
        redis=redis,
        context_id=str(context.id),
        payload={"key": context.key, "value": context.value}
    )

    return context


@router.get("/", response_model=list[ContextSummary])
async def list_contexts(
    context_type: str | None = Query(None),
    status: ContextStatus | None = Query(None),
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    return await context_service.get_workspace_contexts(
        db=db,
        workspace_id=workspace.id,
        context_type=context_type,
        status=status,
    )


@router.get("/search", response_model=list[ContextSummary])
async def search_contexts(
    query: str = Query(..., min_length=1),
    threshold: float = Query(0.75, ge=0.0, le=1.0),
    top_k: int = Query(5, ge=1, le=20),
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    return await context_service.search_similar_contexts(
        db=db,
        query=query,
        workspace_id=workspace.id,
        threshold=threshold,
        top_k=top_k
    )


@router.get("/{context_id}", response_model=ContextResponse)
async def get_context(
    context_id: uuid.UUID,
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    await redis_service.get_cached_context(redis, str(context_id))
    return await context_service.get_context_by_id(db, context_id, workspace.id)


@router.patch("/{context_id}/status", response_model=ContextResponse)
async def update_context_status(
    context_id: uuid.UUID,
    data: ContextStatusUpdate,
    agent_id: uuid.UUID = Query(...),
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    context = await context_service.update_context_status(
        db=db,
        context_id=context_id,
        agent_id=agent_id,
        workspace_id=workspace.id,
        data=data
    )
    await redis_service.invalidate_cached_context(redis, str(context_id))
    return context


@router.patch("/{context_id}/visibility", response_model=ContextResponse)
async def update_context_visibility(
    context_id: uuid.UUID,
    data: ContextVisibilityUpdate,
    agent_id: uuid.UUID = Query(...),
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    context = await context_service.update_context_visibility(
        db=db,
        context_id=context_id,
        agent_id=agent_id,
        workspace_id=workspace.id,
        data=data
    )
    await redis_service.invalidate_cached_context(redis, str(context_id))
    return context


@router.get("/{context_id}/lineage", response_model=list[LineageResponse])
async def get_context_lineage(
    context_id: uuid.UUID,
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    await context_service.get_context_by_id(db, context_id, workspace.id)
    return await lineage_service.get_context_lineage(db, context_id)