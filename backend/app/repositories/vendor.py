from decimal import Decimal, InvalidOperation
from uuid import UUID
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from app.models.vendor import Vendor
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.repositories.base import BaseRepository


class VendorRepository(BaseRepository[Vendor]):
    def __init__(self, db: AsyncSession):
        super().__init__(Vendor, db)

    @staticmethod
    def _to_decimal(value: object) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

    @staticmethod
    def _score_to_trust(score: Decimal) -> Decimal:
        bounded_score = min(Decimal("100"), max(Decimal("0"), score))
        return bounded_score / Decimal("100")

    async def _metric_map(self, vendor_ids: list[UUID]) -> dict[UUID, tuple[int, Decimal | None, Decimal | None]]:
        if not vendor_ids:
            return {}

        rows = await self.db.execute(
            select(
                Invoice.vendor_id.label("vendor_id"),
                func.count(Invoice.id).label("invoice_count"),
                func.avg(Invoice.total).label("avg_invoice_amount"),
                func.avg(func.coalesce(Invoice.confidence_score, 0)).label("avg_invoice_score"),
            )
            .where(Invoice.vendor_id.in_(vendor_ids))
            .group_by(Invoice.vendor_id)
        )

        metric_map: dict[UUID, tuple[int, Decimal | None, Decimal | None]] = {}
        for vendor_id, invoice_count, avg_invoice_amount, avg_invoice_score in rows.all():
            if vendor_id is None:
                continue
            metric_map[vendor_id] = (
                int(invoice_count or 0),
                self._to_decimal(avg_invoice_amount),
                self._to_decimal(avg_invoice_score),
            )
        return metric_map

    async def _hydrate_metrics(self, vendors: list[Vendor]) -> list[Vendor]:
        metric_map = await self._metric_map([vendor.id for vendor in vendors])

        for vendor in vendors:
            invoice_count, avg_invoice_amount, avg_invoice_score = metric_map.get(
                vendor.id,
                (0, None, None),
            )

            set_committed_value(vendor, "invoice_count", invoice_count)
            set_committed_value(vendor, "avg_invoice_amount", avg_invoice_amount)

            # Baseline trust score for vendors with no invoices.
            trust_score = Decimal("0.5") if invoice_count == 0 else self._score_to_trust(
                avg_invoice_score or Decimal("0")
            )
            set_committed_value(vendor, "trust_score", trust_score)

        return vendors

    async def get_by_id(self, id: UUID) -> Vendor | None:
        vendor = await super().get_by_id(id)
        if vendor is None:
            return None
        await self._hydrate_metrics([vendor])
        return vendor

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Vendor]:
        vendors = await super().get_all(skip, limit)
        return await self._hydrate_metrics(vendors)

    async def get_by_name(self, name: str) -> Vendor | None:
        result = await self.db.execute(select(Vendor).where(Vendor.name == name))
        vendor = result.scalar_one_or_none()
        if vendor is None:
            return None
        await self._hydrate_metrics([vendor])
        return vendor

    async def get_by_email(self, email: str) -> Vendor | None:
        result = await self.db.execute(select(Vendor).where(Vendor.email == email))
        vendor = result.scalar_one_or_none()
        if vendor is None:
            return None
        await self._hydrate_metrics([vendor])
        return vendor

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
