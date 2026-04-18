import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workspace import Workspace
from app.schemas.workspace import WorkspaceUpdate
from app.utils.exceptions import WorkspaceNotFoundException


async def get_workspace_by_owner(
    db: AsyncSession,
    owner_id: uuid.UUID
) -> Workspace:
    result = await db.execute(
        select(Workspace)
        .where(Workspace.owner_id == owner_id)
        .options(selectinload(Workspace.agents))
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise WorkspaceNotFoundException(str(owner_id))
    return workspace


async def get_workspace_by_id(
    db: AsyncSession,
    workspace_id: uuid.UUID
) -> Workspace:
    result = await db.execute(
        select(Workspace)
        .where(Workspace.id == workspace_id)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise WorkspaceNotFoundException(str(workspace_id))
    return workspace


async def get_workspace_by_slug(
    db: AsyncSession,
    slug: str
) -> Workspace:
    result = await db.execute(
        select(Workspace)
        .where(Workspace.slug == slug)
    )
    workspace = result.scalar_one_or_none()
    if not workspace:
        raise WorkspaceNotFoundException(slug)
    return workspace


async def update_workspace(
    db: AsyncSession,
    owner_id: uuid.UUID,
    data: WorkspaceUpdate
) -> Workspace:
    workspace = await get_workspace_by_owner(db, owner_id)
    if data.name is not None:
        workspace.name = data.name
    if data.description is not None:
        workspace.description = data.description
    await db.flush()
    await db.refresh(workspace)
    return workspace