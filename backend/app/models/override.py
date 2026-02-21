import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Override(Base):
    __tablename__ = "overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, unique=True)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)
    agent_recommendation = Column(Text, nullable=False)
    human_decision = Column(Text, nullable=True)
    agreed = Column(Boolean, nullable=True)
    override_reason = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # One override → one invoice
    invoice = relationship("Invoice", back_populates="override")
    # Many overrides → one vendor
    vendor = relationship("Vendor", back_populates="overrides")
