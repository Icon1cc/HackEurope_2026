import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, unique=True)
    stripe_payout_id = Column(Text, nullable=True)
    amount = Column(Numeric, nullable=False)
    currency = Column(Text, nullable=False, default="EUR")
    status = Column(String(20), nullable=False, default="initiated", index=True)
    initiated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    # One payment → one invoice
    invoice = relationship("Invoice", back_populates="payment")
