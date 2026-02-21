import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
# {
#   "invoice_number": "INV-2026-001",
#   "invoice_date": "February 21, 2026",
#   "due_date": null,
#   "vendor_name": "Cloud Services Provider Ltd.",
#   "vendor_address": "123 Tech Park, Silicon Valley, CA 94043",
#   "client_name": "Example Corp.",
#   "client_address": "456 Business Blvd, New York, NY 10001",
#   "line_items": [
#     {
#       "description": "AWS EC2 Instance",
#       "quantity": 730.0,
#       "unit_price": 0.046,
#       "total_price": 33.58,
#       "unit": null
#     },
#     {
#       "description": "AWS S3 Storage",
#       "quantity": 1000.0,
#       "unit_price": 0.023,
#       "total_price": 23.0,
#       "unit": null
#     },
#     {
#       "description": "AWS RDS Database",
#       "quantity": 1.0,
#       "unit_price": 150.0,
#       "total_price": 150.0,
#       "unit": null
#     }
#   ],
#   "subtotal": 206.58,
#   "tax": 41.32,
#   "total": 247.9,
#   "currency": "USD"
# }

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id"), nullable=True)
    invoice_number = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    vendor_name = Column(Text, nullable=True)
    vendor_address = Column(Text, nullable=True)
    client_name = Column(Text, nullable=True)
    client_address = Column(Text, nullable=True)
    subtotal = Column(Numeric, nullable=True)
    tax = Column(Numeric, nullable=True)
    total = Column(Numeric, nullable=True)
    currency = Column(String(10), nullable=True, default="EUR")
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
    # One invoice → many items
    items = relationship("Item", back_populates="invoice", cascade="all, delete-orphan")