import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services import agent_service


router = APIRouter(prefix="/agents", tags=["Agents"])


@router.post("/", response_model=AgentResponse, status_code=201)
async def register_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.create_agent(db, data)


@router.get("/", response_model=list[AgentResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.get_all_agents(db)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.get_agent_by_id(db, agent_id)


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: uuid.UUID,
    data: AgentUpdate,
    db: AsyncSession = Depends(get_db)
):
    return await agent_service.update_agent(db, agent_id, data)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    await agent_service.delete_agent(db, agent_id)