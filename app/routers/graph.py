from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.routers.auth import get_current_user_id
from app.services import graph_service, workspace_service


router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/", summary="Get your workspace graph")
async def get_workspace_graph(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    workspace = await workspace_service.get_workspace_by_owner(
        db, uuid.UUID(user_id)
    )
    return await graph_service.build_workspace_graph(db, workspace.id)


@router.get("/public", summary="Get global public graph")
async def get_public_graph(
    db: AsyncSession = Depends(get_db)
):
    return await graph_service.build_public_graph(db)