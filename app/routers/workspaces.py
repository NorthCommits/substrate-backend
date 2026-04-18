from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.routers.auth import get_current_user_id
from app.schemas.workspace import WorkspaceResponse, WorkspaceUpdate
from app.services import workspace_service


router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("/me", response_model=WorkspaceResponse)
async def get_my_workspace(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await workspace_service.get_workspace_by_owner(
        db, uuid.UUID(user_id)
    )


@router.patch("/me", response_model=WorkspaceResponse)
async def update_my_workspace(
    data: WorkspaceUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    return await workspace_service.update_workspace(
        db, uuid.UUID(user_id), data
    )


@router.get("/{slug}", response_model=WorkspaceResponse)
async def get_workspace_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    return await workspace_service.get_workspace_by_slug(db, slug)