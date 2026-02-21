from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class MarketDataCreate(BaseModel):
    name: str
    category: str
    price_per_unit: Decimal


class MarketDataUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    price_per_unit: Decimal | None = None


class MarketDataResponse(BaseModel):
    id: UUID
    name: str
    category: str
    price_per_unit: Decimal
    timestamp: datetime

    model_config = {"from_attributes": True}
