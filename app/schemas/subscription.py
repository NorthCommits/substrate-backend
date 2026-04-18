import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.agent import AgentSummary


class SubscriptionCreate(BaseModel):
    agent_id: uuid.UUID
    context_type: str = Field(..., min_length=1, max_length=100)
    producer_id: uuid.UUID | None = None


class SubscriptionResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    context_type: str
    producer_id: uuid.UUID | None
    workspace_id: uuid.UUID
    is_active: bool
    created_at: datetime
    agent: AgentSummary

    model_config = {"from_attributes": True}