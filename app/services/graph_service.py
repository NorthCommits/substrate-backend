import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent import Agent
from app.models.context import Context
from app.models.subscription import Subscription


async def build_graph(db: AsyncSession) -> dict:
    agents_result = await db.execute(
        select(Agent).order_by(Agent.created_at.desc())
    )
    agents = list(agents_result.scalars().all())

    contexts_result = await db.execute(
        select(Context)
        .options(selectinload(Context.producer))
        .order_by(Context.created_at.desc())
    )
    contexts = list(contexts_result.scalars().all())

    subscriptions_result = await db.execute(
        select(Subscription)
        .where(Subscription.is_active == True)
        .options(selectinload(Subscription.agent))
        .order_by(Subscription.created_at.desc())
    )
    subscriptions = list(subscriptions_result.scalars().all())

    nodes = []
    edges = []

    for agent in agents:
        nodes.append({
            "id": str(agent.id),
            "type": "agent",
            "label": agent.name,
            "is_active": agent.is_active,
            "description": agent.description,
        })

    for context in contexts:
        nodes.append({
            "id": str(context.id),
            "type": "context",
            "label": context.key,
            "context_type": context.context_type,
            "status": context.status.value,
        })

        edges.append({
            "id": f"produces-{context.producer_id}-{context.id}",
            "source": str(context.producer_id),
            "target": str(context.id),
            "label": "produces",
        })

    for subscription in subscriptions:
        edges.append({
            "id": f"subscribes-{subscription.agent_id}-{subscription.context_type}",
            "source": str(subscription.agent_id),
            "target": str(subscription.producer_id) if subscription.producer_id else subscription.context_type,
            "label": f"subscribes to {subscription.context_type}",
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "total_agents": len(agents),
            "active_agents": sum(1 for a in agents if a.is_active),
            "total_contexts": len(contexts),
            "active_contexts": sum(1 for c in contexts if c.status.value == "active"),
            "total_subscriptions": len(subscriptions),
        }
    }