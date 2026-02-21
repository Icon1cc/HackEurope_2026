import asyncio
import logging
from collections import defaultdict
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.repositories.cloud_pricing import CloudPricingRepository
from app.repositories.market_data import MarketDataRepository
from app.schemas.cloud_pricing import (
    CloudPricingResponse,
    InvoiceCheckRequest,
    InvoiceCheckResponse,
    InvoiceLineItem,
    LineItemResult,
    SyncStatus,
)
from app.pricing.fetcher import fetch_all
from app.pricing.normalizer import normalize_all

logger = logging.getLogger(__name__)


class CloudPricingService:
    def __init__(self, repo: CloudPricingRepository, market_data_repo: Optional[MarketDataRepository] = None):
        self.repo = repo
        self.market_data_repo = market_data_repo

    async def get_pricing(self, pricing_id: UUID) -> Optional[CloudPricingResponse]:
        item = await self.repo.get_by_id(pricing_id)
        return CloudPricingResponse.model_validate(item) if item else None

    async def get_filtered(
        self,
        vendor: Optional[str] = None,
        category: Optional[str] = None,
        region: Optional[str] = None,
        instance_type: Optional[str] = None,
        service_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[CloudPricingResponse]:
        items = await self.repo.get_filtered(
            vendor=vendor, category=category, region=region,
            instance_type=instance_type, service_name=service_name,
            skip=skip, limit=limit,
        )
        return [CloudPricingResponse.model_validate(i) for i in items]

    async def trigger_sync(self) -> SyncStatus:
        """Fetch → normalise → upsert. Runs fetcher in a thread (sync HTTP)."""
        logger.info("Starting full pricing sync …")
        payloads = await asyncio.to_thread(fetch_all)
        records = normalize_all(payloads)
        logger.info("Normalised %d records across all sources", len(records))

        if records:
            affected = await self.repo.upsert_records(records)
            logger.info("Sync complete — %d rows upserted", affected)

            # Populate market_data with aggregated benchmarks
            await self._populate_market_data(records)

        return await self.get_sync_status()

    async def _populate_market_data(self, records: list[dict]) -> None:
        """Create market_data entries from synced cloud pricing records."""
        if not self.market_data_repo:
            return

        # Aggregate: average price_per_unit grouped by (service_name, category)
        buckets: dict[tuple[str, str], list[Decimal]] = defaultdict(list)
        for r in records:
            ppu = r.get("price_per_unit")
            if ppu is None or ppu == 0:
                continue
            key = (r.get("service_name", "Unknown"), r.get("category", "Other"))
            buckets[key].append(Decimal(str(ppu)))

        count = 0
        for (service_name, category), prices in buckets.items():
            avg_price = sum(prices) / len(prices)
            await self.market_data_repo.create(
                name=service_name,
                category=category,
                price_per_unit=avg_price,
            )
            count += 1

        logger.info("Populated %d market_data benchmark entries", count)

    async def get_sync_status(self) -> SyncStatus:
        data = await self.repo.get_sync_status()
        return SyncStatus(**data)

    async def check_invoice(self, req: InvoiceCheckRequest) -> InvoiceCheckResponse:
        """Compare invoice line items against stored pricing catalogue."""
        line_results: list[LineItemResult] = []
        total_billed = Decimal("0")
        total_expected = Decimal("0")

        for item in req.items:
            total_billed += item.billed_amount
            match = await self.repo.find_best_match(
                vendor=item.vendor,
                sku_id=item.sku_id,
                instance_type=item.instance_type,
                region=item.region,
            )

            if match is None:
                line_results.append(LineItemResult(
                    line=item, matched_sku=None,
                    expected_amount=None, billed_amount=item.billed_amount,
                    discrepancy=None, discrepancy_pct=None, status="NO_MATCH",
                ))
                continue

            expected = match.price_per_hour * item.hours
            total_expected += expected
            discrepancy = item.billed_amount - expected
            pct = (discrepancy / expected * 100).quantize(Decimal("0.01")) if expected else None

            if abs(discrepancy) < Decimal("0.01"):
                status = "OK"
            elif discrepancy > 0:
                status = "OVERBILLED"
            else:
                status = "UNDERBILLED"

            line_results.append(LineItemResult(
                line=item,
                matched_sku=CloudPricingResponse.model_validate(match),
                expected_amount=expected.quantize(Decimal("0.0001")),
                billed_amount=item.billed_amount,
                discrepancy=discrepancy.quantize(Decimal("0.0001")),
                discrepancy_pct=pct,
                status=status,
            ))

        return InvoiceCheckResponse(
            total_billed=total_billed,
            total_expected=total_expected,
            total_discrepancy=(total_billed - total_expected).quantize(Decimal("0.0001")),
            items=line_results,
        )
