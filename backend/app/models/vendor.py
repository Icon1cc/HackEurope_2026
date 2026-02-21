import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    category = Column(Text, nullable=False, default="computing", index=True)
    email = Column(Text, nullable=True)
    registered_iban = Column(Text, nullable=True)
    known_iban_changes = Column(JSONB, nullable=True)
    avg_invoice_amount = Column(Numeric, nullable=True)
    invoice_count = Column(Integer, nullable=False, default=0)
    trust_score = Column(Numeric, nullable=False, default=0.5)
    auto_approve_threshold = Column(Integer, nullable=False, default=85)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # One vendor → many invoices
    invoices = relationship("Invoice", back_populates="vendor")
    # One vendor → many overrides
    overrides = relationship("Override", back_populates="vendor")
