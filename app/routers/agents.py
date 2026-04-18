import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.api_key_auth import get_workspace_from_api_key
from app.models.workspace import Workspace
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services import agent_service


router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("/", response_model=AgentResponse, status_code=201)
async def register_agent(
    data: AgentCreate,
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.create_agent(db, workspace.id, data)


@router.get("/", response_model=list[AgentResponse])
async def list_agents(
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.get_workspace_agents(db, workspace.id)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.get_agent_by_id(db, agent_id, workspace.id)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.update_agent(db, agent_id, workspace.id, data)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID,
    workspace: Workspace = Depends(get_workspace_from_api_key),
    db: AsyncSession = Depends(get_db)
):
    await agent_service.delete_agent(db, agent_id, workspace.id)