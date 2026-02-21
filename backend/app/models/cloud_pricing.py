import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, Numeric, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class CloudPricing(Base):
    """
    Unified cloud pricing record.
    One row per billable SKU/meter across AWS, Azure, and GCP.
    """

    __tablename__ = "cloud_pricing"
    __table_args__ = (
        UniqueConstraint("vendor", "sku_id", "source_api", name="uq_pricing_vendor_sku_source"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # identity
    vendor = Column(String(16), nullable=False, index=True)
    service_name = Column(Text, nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    sku_id = Column(Text, nullable=False)
    description = Column(Text, nullable=True)

    # location / spec
    region = Column(Text, nullable=True, index=True)
    instance_type = Column(Text, nullable=True, index=True)
    operating_system = Column(Text, nullable=True)

    # pricing
    price_per_unit = Column(Numeric(20, 10), nullable=False)
    unit = Column(Text, nullable=False)
    price_per_hour = Column(Numeric(20, 10), nullable=True)
    currency = Column(String(8), nullable=False, default="USD")
    effective_date = Column(DateTime(timezone=True), nullable=True)

    # provenance
    raw_attributes = Column(JSONB, nullable=True)
    source_api = Column(String(64), nullable=False)

    # timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
