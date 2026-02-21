import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False, index=True)
    category = Column(Text, nullable=False, index=True)
    price_per_unit = Column(Numeric, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
