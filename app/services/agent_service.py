import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate
from app.utils.exceptions import AgentNotFoundException, AgentNameConflictException


async def create_agent(db: AsyncSession, data: AgentCreate) -> Agent:
    existing = await db.execute(
        select(Agent).where(Agent.name == data.name)
    )
    if existing.scalar_one_or_none():
        raise AgentNameConflictException(data.name)

    agent = Agent(
        id=uuid.uuid4(),
        name=data.name,
        description=data.description,
    )
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


async def get_agent_by_id(db: AsyncSession, agent_id: uuid.UUID) -> Agent:
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise AgentNotFoundException(str(agent_id))
    return agent


async def get_all_agents(db: AsyncSession) -> list[Agent]:
    result = await db.execute(
        select(Agent).order_by(Agent.created_at.desc())
    )
    return list(result.scalars().all())


async def update_agent(
    db: AsyncSession,
    agent_id: uuid.UUID,
    data: AgentUpdate
) -> Agent:
    agent = await get_agent_by_id(db, agent_id)
    if data.description is not None:
        agent.description = data.description
    if data.is_active is not None:
        agent.is_active = data.is_active
    await db.flush()
    await db.refresh(agent)
    return agent


async def delete_agent(db: AsyncSession, agent_id: uuid.UUID) -> None:
    agent = await get_agent_by_id(db, agent_id)
    await db.delete(agent)
    await db.flush()