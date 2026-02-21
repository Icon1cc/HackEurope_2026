from uuid import UUID
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cloud_pricing import CloudPricing
from app.repositories.base import BaseRepository


class CloudPricingRepository(BaseRepository[CloudPricing]):
    def __init__(self, db: AsyncSession):
        super().__init__(CloudPricing, db)

    async def get_filtered(
        self,
        vendor: Optional[str] = None,
        category: Optional[str] = None,
        region: Optional[str] = None,
        instance_type: Optional[str] = None,
        service_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CloudPricing]:
        q = select(CloudPricing)
        if vendor:
            q = q.where(CloudPricing.vendor == vendor.lower())
        if category:
            q = q.where(CloudPricing.category == category)
        if region:
            q = q.where(CloudPricing.region.ilike(f"%{region}%"))
        if instance_type:
            q = q.where(CloudPricing.instance_type.ilike(f"%{instance_type}%"))
        if service_name:
            q = q.where(CloudPricing.service_name.ilike(f"%{service_name}%"))
        q = q.order_by(CloudPricing.vendor, CloudPricing.service_name).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def upsert_records(self, records: list[dict]) -> int:
        """Upsert normalised pricing records. Returns total rows affected."""
        if not records:
            return 0

        # Deduplicate by (vendor, sku_id, source_api) — keep last occurrence
        seen: dict[tuple, dict] = {}
        for r in records:
            key = (r.get("vendor"), r.get("sku_id"), r.get("source_api"))
            seen[key] = r
        records = list(seen.values())

        table = CloudPricing.__table__
        chunk_size = 500
        total_affected = 0

        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            stmt = pg_insert(table).values(chunk)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_pricing_vendor_sku_source",
                set_={
                    "service_name": stmt.excluded.service_name,
                    "category": stmt.excluded.category,
                    "description": stmt.excluded.description,
                    "region": stmt.excluded.region,
                    "instance_type": stmt.excluded.instance_type,
                    "operating_system": stmt.excluded.operating_system,
                    "price_per_unit": stmt.excluded.price_per_unit,
                    "unit": stmt.excluded.unit,
                    "price_per_hour": stmt.excluded.price_per_hour,
                    "currency": stmt.excluded.currency,
                    "effective_date": stmt.excluded.effective_date,
                    "raw_attributes": stmt.excluded.raw_attributes,
                    "updated_at": func.now(),
                },
            )
            result = await self.db.execute(stmt)
            total_affected += result.rowcount
            await self.db.commit()

        return total_affected

    async def get_sync_status(self) -> dict:
        """Return aggregate stats about current pricing data."""
        total_q = await self.db.execute(select(func.count(CloudPricing.id)))
        total = total_q.scalar() or 0

        vendor_q = await self.db.execute(
            select(CloudPricing.vendor, func.count(CloudPricing.id).label("cnt"))
            .group_by(CloudPricing.vendor)
        )
        by_vendor = {row.vendor: row.cnt for row in vendor_q.all()}

        cat_q = await self.db.execute(
            select(CloudPricing.category, func.count(CloudPricing.id).label("cnt"))
            .group_by(CloudPricing.category)
        )
        by_category = {row.category: row.cnt for row in cat_q.all()}

        last_q = await self.db.execute(select(func.max(CloudPricing.updated_at)))
        last_sync = last_q.scalar()

        return {
            "last_sync": last_sync,
            "total_skus": total,
            "by_vendor": by_vendor,
            "by_category": by_category,
            "message": "OK" if total > 0 else "No data yet — trigger a sync via POST /pricing/sync",
        }

    async def find_best_match(self, vendor: str, sku_id: Optional[str], instance_type: Optional[str], region: Optional[str]) -> Optional[CloudPricing]:
        """Find the best matching hourly SKU for invoice checking."""
        vendor = vendor.lower()
        base = select(CloudPricing).where(
            CloudPricing.vendor == vendor,
            CloudPricing.price_per_hour.isnot(None),
        )

        # 1 – exact SKU
        if sku_id:
            result = await self.db.execute(base.where(CloudPricing.sku_id == sku_id))
            match = result.scalar_one_or_none()
            if match:
                return match

        # 2 – instance_type + region
        if instance_type and region:
            result = await self.db.execute(
                base.where(
                    CloudPricing.instance_type.ilike(instance_type),
                    CloudPricing.region.ilike(f"%{region}%"),
                )
            )
            match = result.scalar_one_or_none()
            if match:
                return match

        # 3 – instance_type only
        if instance_type:
            result = await self.db.execute(
                base.where(CloudPricing.instance_type.ilike(instance_type))
            )
            match = result.scalars().first()
            if match:
                return match

        return None
