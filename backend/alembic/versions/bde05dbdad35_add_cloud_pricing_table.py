"""add_cloud_pricing_table

Revision ID: bde05dbdad35
Revises: 
Create Date: 2026-02-21 23:42:34.370909

"""
from alembic import op, context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'bde05dbdad35'
down_revision = None
branch_labels = None
depends_on = None


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _create_cloud_pricing_table() -> None:
    op.create_table(
        "cloud_pricing",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("vendor", sa.String(length=16), nullable=False),
        sa.Column("service_name", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("sku_id", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("region", sa.Text(), nullable=True),
        sa.Column("instance_type", sa.Text(), nullable=True),
        sa.Column("operating_system", sa.Text(), nullable=True),
        sa.Column("price_per_unit", sa.Numeric(precision=20, scale=10), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("price_per_hour", sa.Numeric(precision=20, scale=10), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_api", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor", "sku_id", "source_api", name="uq_pricing_vendor_sku_source"),
    )
    op.create_index(op.f("ix_cloud_pricing_category"), "cloud_pricing", ["category"], unique=False)
    op.create_index(op.f("ix_cloud_pricing_instance_type"), "cloud_pricing", ["instance_type"], unique=False)
    op.create_index(op.f("ix_cloud_pricing_region"), "cloud_pricing", ["region"], unique=False)
    op.create_index(op.f("ix_cloud_pricing_service_name"), "cloud_pricing", ["service_name"], unique=False)
    op.create_index(op.f("ix_cloud_pricing_vendor"), "cloud_pricing", ["vendor"], unique=False)


def upgrade() -> None:
    if context.is_offline_mode():
        _create_cloud_pricing_table()
        op.add_column("invoices", sa.Column("invoice_number", sa.Text(), nullable=True))
        op.add_column("invoices", sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))
        op.add_column("invoices", sa.Column("vendor_name", sa.Text(), nullable=True))
        op.add_column("invoices", sa.Column("vendor_address", sa.Text(), nullable=True))
        op.add_column("invoices", sa.Column("client_name", sa.Text(), nullable=True))
        op.add_column("invoices", sa.Column("client_address", sa.Text(), nullable=True))
        op.add_column("invoices", sa.Column("subtotal", sa.Numeric(), nullable=True))
        op.add_column("invoices", sa.Column("tax", sa.Numeric(), nullable=True))
        op.add_column("invoices", sa.Column("total", sa.Numeric(), nullable=True))
        op.add_column("invoices", sa.Column("currency", sa.String(length=10), nullable=True))
        op.add_column("vendors", sa.Column("vendor_address", sa.Text(), nullable=True))
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Fresh local DBs may have no baseline migration history.
    required_tables = ("clients", "vendors", "invoices", "items", "payments", "overrides", "market_data")
    if any(not inspector.has_table(table_name) for table_name in required_tables):
        from app.core.database import Base
        import app.models  # noqa: F401

        Base.metadata.create_all(bind=bind)
        inspector = sa.inspect(bind)

    if not inspector.has_table("cloud_pricing"):
        _create_cloud_pricing_table()
        inspector = sa.inspect(bind)

    if inspector.has_table("invoices"):
        if not _column_exists(inspector, "invoices", "invoice_number"):
            op.add_column("invoices", sa.Column("invoice_number", sa.Text(), nullable=True))
        if not _column_exists(inspector, "invoices", "due_date"):
            op.add_column("invoices", sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))
        if not _column_exists(inspector, "invoices", "vendor_name"):
            op.add_column("invoices", sa.Column("vendor_name", sa.Text(), nullable=True))
        if not _column_exists(inspector, "invoices", "vendor_address"):
            op.add_column("invoices", sa.Column("vendor_address", sa.Text(), nullable=True))
        if not _column_exists(inspector, "invoices", "client_name"):
            op.add_column("invoices", sa.Column("client_name", sa.Text(), nullable=True))
        if not _column_exists(inspector, "invoices", "client_address"):
            op.add_column("invoices", sa.Column("client_address", sa.Text(), nullable=True))
        if not _column_exists(inspector, "invoices", "subtotal"):
            op.add_column("invoices", sa.Column("subtotal", sa.Numeric(), nullable=True))
        if not _column_exists(inspector, "invoices", "tax"):
            op.add_column("invoices", sa.Column("tax", sa.Numeric(), nullable=True))
        if not _column_exists(inspector, "invoices", "total"):
            op.add_column("invoices", sa.Column("total", sa.Numeric(), nullable=True))
        if not _column_exists(inspector, "invoices", "currency"):
            op.add_column("invoices", sa.Column("currency", sa.String(length=10), nullable=True))

    if inspector.has_table("vendors") and not _column_exists(inspector, "vendors", "vendor_address"):
        op.add_column("vendors", sa.Column("vendor_address", sa.Text(), nullable=True))


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_column("vendors", "vendor_address")
        op.drop_column("invoices", "currency")
        op.drop_column("invoices", "total")
        op.drop_column("invoices", "tax")
        op.drop_column("invoices", "subtotal")
        op.drop_column("invoices", "client_address")
        op.drop_column("invoices", "client_name")
        op.drop_column("invoices", "vendor_address")
        op.drop_column("invoices", "vendor_name")
        op.drop_column("invoices", "due_date")
        op.drop_column("invoices", "invoice_number")
        op.drop_index(op.f("ix_cloud_pricing_vendor"), table_name="cloud_pricing")
        op.drop_index(op.f("ix_cloud_pricing_service_name"), table_name="cloud_pricing")
        op.drop_index(op.f("ix_cloud_pricing_region"), table_name="cloud_pricing")
        op.drop_index(op.f("ix_cloud_pricing_instance_type"), table_name="cloud_pricing")
        op.drop_index(op.f("ix_cloud_pricing_category"), table_name="cloud_pricing")
        op.drop_table("cloud_pricing")
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("vendors") and _column_exists(inspector, "vendors", "vendor_address"):
        op.drop_column("vendors", "vendor_address")

    if inspector.has_table("invoices"):
        for column_name in (
            "currency",
            "total",
            "tax",
            "subtotal",
            "client_address",
            "client_name",
            "vendor_address",
            "vendor_name",
            "due_date",
            "invoice_number",
        ):
            if _column_exists(inspector, "invoices", column_name):
                op.drop_column("invoices", column_name)

    if inspector.has_table("cloud_pricing"):
        existing_indexes = {index["name"] for index in inspector.get_indexes("cloud_pricing")}
        for index_name in (
            op.f("ix_cloud_pricing_vendor"),
            op.f("ix_cloud_pricing_service_name"),
            op.f("ix_cloud_pricing_region"),
            op.f("ix_cloud_pricing_instance_type"),
            op.f("ix_cloud_pricing_category"),
        ):
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="cloud_pricing")
        op.drop_table("cloud_pricing")
