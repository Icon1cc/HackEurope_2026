import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Text, Integer, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
# {
#   "invoice_number": "INV-2026-001",
#   "invoice_date": "February 21, 2026",
#   "due_date": null,
#   "vendor_name": "Example Vendor GmbH",
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
    vendor_address = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # One vendor → many invoices
    invoices = relationship("Invoice", back_populates="vendor")
    # One vendor → many overrides
    overrides = relationship("Override", back_populates="vendor")
