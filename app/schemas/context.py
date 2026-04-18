import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.context import ContextStatus
from app.schemas.agent import AgentSummary


class ContextPublish(BaseModel):
    key: str = Field(..., min_length=1, max_length=255)
    value: dict = Field(...)
    context_type: str = Field(..., min_length=1, max_length=100)
    producer_id: uuid.UUID


class ContextStatusUpdate(BaseModel):
    status: ContextStatus


class ContextResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: dict
    context_type: str
    status: ContextStatus
    producer_id: uuid.UUID
    producer: AgentSummary
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ContextSummary(BaseModel):
    id: uuid.UUID
    key: str
    context_type: str
    status: ContextStatus
    producer_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}