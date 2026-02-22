from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.services.vendor import VendorService
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse, VendorSummary
from app.core.dependencies import get_vendor_service, get_current_user

router = APIRouter(prefix="/vendors", tags=["vendors"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[VendorResponse])
async def get_all(skip: int = 0, limit: int = 100, service: VendorService = Depends(get_vendor_service)):
    return await service.get_all_vendors(skip, limit)


@router.get("/{id}/summary", response_model=VendorSummary)
async def get_summary(id: UUID, service: VendorService = Depends(get_vendor_service)):
    summary = await service.get_vendor_summary(id)
    if not summary:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return summary


@router.get("/{id}", response_model=VendorResponse)
async def get_one(id: UUID, service: VendorService = Depends(get_vendor_service)):
    vendor = await service.get_vendor(id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.post("/", response_model=VendorResponse, status_code=201)
async def create(data: VendorCreate, service: VendorService = Depends(get_vendor_service)):
    return await service.create_vendor(data)


@router.patch("/{id}", response_model=VendorResponse)
async def update(id: UUID, data: VendorUpdate, service: VendorService = Depends(get_vendor_service)):
    vendor = await service.update_vendor(id, data)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.delete("/{id}", status_code=204)
async def delete(id: UUID, service: VendorService = Depends(get_vendor_service)):
    if not await service.delete_vendor(id):
        raise HTTPException(status_code=404, detail="Vendor not found")
