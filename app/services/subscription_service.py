import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate
from app.services.agent_service import get_agent_by_id
from app.utils.exceptions import (
    SubscriptionNotFoundException,
    SubscriptionConflictException
)


async def create_subscription(
    db: AsyncSession,
    data: SubscriptionCreate
) -> Subscription:
    await get_agent_by_id(db, data.agent_id)

    existing = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.agent_id == data.agent_id,
                Subscription.context_type == data.context_type,
                Subscription.producer_id == data.producer_id,
                Subscription.is_active == True
            )
        )
    )
    if existing.scalar_one_or_none():
        raise SubscriptionConflictException()

    subscription = Subscription(
        id=uuid.uuid4(),
        agent_id=data.agent_id,
        context_type=data.context_type,
        producer_id=data.producer_id,
        is_active=True
    )
    db.add(subscription)
    await db.flush()
    await db.refresh(subscription, ["agent"])
    return subscription


async def get_agent_subscriptions(
    db: AsyncSession,
    agent_id: uuid.UUID
) -> list[Subscription]:
    await get_agent_by_id(db, agent_id)
    result = await db.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.agent_id == agent_id,
                Subscription.is_active == True
            )
        )
        .options(selectinload(Subscription.agent))
        .order_by(Subscription.created_at.desc())
    )
    return list(result.scalars().all())


async def deactivate_subscription(
    db: AsyncSession,
    subscription_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise SubscriptionNotFoundException(str(subscription_id))
    subscription.is_active = False
    await db.flush()


async def get_subscribers_for_context_type(
    db: AsyncSession,
    context_type: str,
    producer_id: uuid.UUID
) -> list[Subscription]:
    result = await db.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.context_type == context_type,
                Subscription.is_active == True,
                (Subscription.producer_id == producer_id) |
                (Subscription.producer_id.is_(None))
            )
        )
        .options(selectinload(Subscription.agent))
    )
    return list(result.scalars().all())