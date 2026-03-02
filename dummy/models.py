"""
pricing/models.py
SQLAlchemy model for the unified cloud_pricing table.
"""

from sqlalchemy import (
    Column, Integer, Numeric, String, Text,
    DateTime, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class CloudPricing(Base):
    """
    Unified cloud pricing record.

    One row per billable SKU/meter across AWS, Azure, and GCP.

    Fields
    ------
    vendor              : aws | azure | gcp
    service_name        : human-readable service (e.g. "Amazon EC2")
    category            : top-level grouping (Compute / Storage / Database / CDN / Other)
    sku_id              : original identifier from the source API
    description         : full price description string from the source
    region              : cloud region (e.g. eu-west-1, westeurope, europe-west9)
    instance_type       : VM/DB instance type when applicable (e.g. m6i.4xlarge)
    operating_system    : Linux | Windows | None
    price_per_unit      : raw price in USD for one unit
    unit                : Hrs | GB | Requests | Lambda-GB-Second | etc.
    price_per_hour      : normalised $/hr – populated only when unit is Hrs/hour/h;
                          NULL for storage, request, or data-transfer SKUs.
                          This is the field used by the invoice checker.
    currency            : always USD in current implementation
    effective_date      : when this price became active
    raw_attributes      : full original record stored as JSONB for auditing
    source_api          : which fetcher produced this row (infracost / aws_ec2 / …)
    created_at          : first inserted
    updated_at          : last upserted (refresh timestamp)
    """

    __tablename__ = "cloud_pricing"
    __table_args__ = (
        # One canonical row per (vendor + sku_id + source).
        # If the same SKU appears in two APIs we keep both.
        UniqueConstraint("vendor", "sku_id", "source_api", name="uq_pricing_vendor_sku_source"),
    )

    id               = Column(Integer, primary_key=True, autoincrement=True)

    # ── identity ──────────────────────────────────────────────────────────
    vendor           = Column(String(16),  nullable=False, index=True)
    service_name     = Column(Text,        nullable=False, index=True)
    category         = Column(String(64),  nullable=False, index=True)
    sku_id           = Column(Text,        nullable=False)
    description      = Column(Text,        nullable=True)

    # ── location / spec ───────────────────────────────────────────────────
    region           = Column(String(64),  nullable=True,  index=True)
    instance_type    = Column(String(64),  nullable=True,  index=True)
    operating_system = Column(String(32),  nullable=True)

    # ── pricing ───────────────────────────────────────────────────────────
    price_per_unit   = Column(Numeric(20, 10), nullable=False)
    unit             = Column(String(64),      nullable=False)
    price_per_hour   = Column(Numeric(20, 10), nullable=True)   # NULL = not an hourly SKU
    currency         = Column(String(8),       nullable=False, default="USD")
    effective_date   = Column(DateTime(timezone=True), nullable=True)

    # ── provenance ────────────────────────────────────────────────────────
    raw_attributes   = Column(JSONB, nullable=True)
    source_api       = Column(String(32), nullable=False)

    # ── timestamps ────────────────────────────────────────────────────────
    created_at       = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at       = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<CloudPricing vendor={self.vendor!r} sku={self.sku_id!r} "
            f"price={self.price_per_unit} {self.unit}>"
        )
