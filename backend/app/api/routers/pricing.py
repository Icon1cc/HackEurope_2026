from uuid import UUID
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.services.cloud_pricing import CloudPricingService
from app.schemas.cloud_pricing import (
    CloudPricingResponse,
    InvoiceCheckRequest,
    InvoiceCheckResponse,
    SyncStatus,
)
from app.core.dependencies import get_cloud_pricing_service, get_current_user

router = APIRouter(prefix="/pricing", tags=["pricing"], dependencies=[Depends(get_current_user)])


# ── Sync ──────────────────────────────────────────────────────────────────

@router.post("/sync", summary="Trigger full pricing data refresh", response_model=SyncStatus)
async def trigger_sync(
    background_tasks: BackgroundTasks,
    service: CloudPricingService = Depends(get_cloud_pricing_service),
):
    """Enqueue a full fetch+normalise+upsert cycle in the background."""
    background_tasks.add_task(service.trigger_sync)
    status = await service.get_sync_status()
    status.message = "Sync triggered — running in background"
    return status


@router.get("/sync/status", summary="Current pricing database status", response_model=SyncStatus)
async def sync_status(service: CloudPricingService = Depends(get_cloud_pricing_service)):
    return await service.get_sync_status()


# ── Browse / query ────────────────────────────────────────────────────────

@router.get("/", summary="List and filter pricing SKUs", response_model=list[CloudPricingResponse])
async def list_pricing(
    vendor: Optional[str] = Query(None, description="aws | azure | gcp"),
    category: Optional[str] = Query(None, description="Compute | Storage | Database | CDN"),
    region: Optional[str] = Query(None, description="Partial match, e.g. eu-west"),
    instance_type: Optional[str] = Query(None, description="e.g. m6i.4xlarge"),
    service_name: Optional[str] = Query(None, description="Partial match on service name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    service: CloudPricingService = Depends(get_cloud_pricing_service),
):
    return await service.get_filtered(
        vendor=vendor, category=category, region=region,
        instance_type=instance_type, service_name=service_name,
        skip=skip, limit=limit,
    )


@router.get("/{pricing_id}", summary="Get a single pricing SKU", response_model=CloudPricingResponse)
async def get_pricing_by_id(
    pricing_id: UUID,
    service: CloudPricingService = Depends(get_cloud_pricing_service),
):
    item = await service.get_pricing(pricing_id)
    if not item:
        raise HTTPException(status_code=404, detail="Pricing record not found")
    return item


# ── Invoice checker ───────────────────────────────────────────────────────

@router.post(
    "/invoice/check",
    summary="Validate invoice line items against stored pricing",
    response_model=InvoiceCheckResponse,
)
async def check_invoice(
    req: InvoiceCheckRequest,
    service: CloudPricingService = Depends(get_cloud_pricing_service),
):
    return await service.check_invoice(req)
