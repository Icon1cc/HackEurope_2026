import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)

    raw_file_url = Column(Text, nullable=True)
    extracted_data = Column(JSONB, nullable=True)
    anomalies = Column(JSONB, nullable=True)
    market_benchmarks = Column(JSONB, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    claude_summary = Column(Text, nullable=True)
    negotiation_email = Column(Text, nullable=True)
    auto_approved = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Many invoices → one vendor
    vendor = relationship("Vendor", back_populates="invoices")
    # Many invoices → one client
    client = relationship("Client", back_populates="invoices")
    # One invoice → one payment
    payment = relationship("Payment", back_populates="invoice", uselist=False)
    # One invoice → one override
    override = relationship("Override", back_populates="invoice", uselist=False)
