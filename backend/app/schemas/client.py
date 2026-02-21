from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ClientCreate(BaseModel):
    name_of_business: str


class ClientUpdate(BaseModel):
    name_of_business: str | None = None


class ClientResponse(BaseModel):
    id: UUID
    name_of_business: str
    created_at: datetime

    model_config = {"from_attributes": True}
