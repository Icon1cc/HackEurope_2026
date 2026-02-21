from uuid import UUID
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.vendor import Vendor
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.repositories.base import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, db: AsyncSession):
        super().__init__(Vendor, db)

    async def get_by_name(self, name: str) -> Vendor | None:
        result = await self.db.execute(select(Vendor).where(Vendor.name == name))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Vendor | None:
        result = await self.db.execute(select(Vendor).where(Vendor.email == email))
        return result.scalar_one_or_none()

    async def get_vendor_summary(self, vendor_id: UUID) -> dict | None:
        vendor = await self.get_by_id(vendor_id)
        if not vendor:
            return None

        result = await self.db.execute(
            select(
                func.count(Invoice.id).label("total"),
                func.count(case(
                    (Invoice.status.in_(["approved", "paid"]), Invoice.id)
                )).label("processed"),
                func.count(case(
                    (Invoice.status.in_(["pending", "flagged", "overcharge"]), Invoice.id)
                )).label("processing"),
                func.count(case(
                    (Invoice.status == "rejected", Invoice.id)
                )).label("rejected"),
            ).where(Invoice.vendor_id == vendor_id)
        )
        counts = result.one()

        amount_result = await self.db.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).select_from(
                Payment.__table__.join(Invoice.__table__, Payment.invoice_id == Invoice.id)
            ).where(
                Invoice.vendor_id == vendor_id,
                Invoice.status.in_(["approved", "paid"]),
            )
        )
        total_accepted = amount_result.scalar()

        return {
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "category": vendor.category,
            "invoices_processed": counts.processed,
            "invoices_processing": counts.processing,
            "invoices_rejected": counts.rejected,
            "total_amount_accepted": total_accepted,
            "trust_score": vendor.trust_score,
        }
