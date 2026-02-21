import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric, nullable=True)
    unit_price = Column(Numeric, nullable=True)
    total_price = Column(Numeric, nullable=True)
    unit = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Many items → one invoice
    invoice = relationship("Invoice", back_populates="items")
