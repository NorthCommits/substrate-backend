import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.subscription import SubscriptionCreate, SubscriptionResponse
from app.services import subscription_service


router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])


@router.post("/", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    return await subscription_service.create_subscription(db, data)


@router.get("/agent/{agent_id}", response_model=list[SubscriptionResponse])
async def get_agent_subscriptions(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    return await subscription_service.get_agent_subscriptions(db, agent_id)


@router.delete("/{subscription_id}", status_code=204)
async def deactivate_subscription(
    subscription_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    await subscription_service.deactivate_subscription(db, subscription_id)