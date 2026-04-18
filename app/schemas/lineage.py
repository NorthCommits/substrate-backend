import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.agent import AgentSummary


class LineageResponse(BaseModel):
    id: uuid.UUID
    context_id: uuid.UUID
    agent_id: uuid.UUID
    action: str
    snapshot: dict | None
    note: str | None
    created_at: datetime
    agent: AgentSummary

    model_config = {"from_attributes": True}