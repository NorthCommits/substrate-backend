import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.routers.auth import get_current_user_id
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse, ApiKeyCreatedResponse
from app.services import api_key_service, workspace_service


router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("/", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_api_key(
    data: ApiKeyCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    workspace = await workspace_service.get_workspace_by_owner(
        db, uuid.UUID(user_id)
    )
    return await api_key_service.create_api_key(db, workspace.id, data)


@router.get("/", response_model=list[ApiKeyResponse])
async def list_api_keys(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    workspace = await workspace_service.get_workspace_by_owner(
        db, uuid.UUID(user_id)
    )
    return await api_key_service.get_workspace_api_keys(db, workspace.id)


@router.delete("/{api_key_id}", status_code=204)
async def revoke_api_key(
    api_key_id: uuid.UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    workspace = await workspace_service.get_workspace_by_owner(
        db, uuid.UUID(user_id)
    )
    await api_key_service.revoke_api_key(db, api_key_id, workspace.id)