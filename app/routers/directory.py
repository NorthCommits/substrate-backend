from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.agent import AgentResponse
from app.schemas.context import ContextSummary
from app.services import agent_service, context_service


router = APIRouter(prefix="/directory", tags=["Directory"])


@router.get("/agents", response_model=list[AgentResponse])
async def list_public_agents(
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.get_all_public_agents(db)


@router.get("/contexts", response_model=list[ContextSummary])
async def list_public_contexts(
    context_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    return await context_service.get_public_contexts(
        db=db,
        context_type=context_type,
    )