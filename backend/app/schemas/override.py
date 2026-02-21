from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class OverrideCreate(BaseModel):
    invoice_id: UUID
    vendor_id: UUID
    agent_recommendation: str


class OverrideUpdate(BaseModel):
    human_decision: str | None = None
    agreed: bool | None = None
    override_reason: str | None = None


class OverrideResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    vendor_id: UUID
    agent_recommendation: str
    human_decision: str | None
    agreed: bool | None
    override_reason: str | None
    timestamp: datetime

    model_config = {"from_attributes": True}
