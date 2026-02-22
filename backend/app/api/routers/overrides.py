from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.services.override import OverrideService
from app.schemas.override import OverrideCreate, OverrideUpdate, OverrideResponse
from app.core.dependencies import get_override_service, get_current_user

router = APIRouter(prefix="/overrides", tags=["overrides"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[OverrideResponse])
async def get_all(skip: int = 0, limit: int = 100, service: OverrideService = Depends(get_override_service)):
    return await service.get_all_overrides(skip, limit)


@router.get("/disagreements", response_model=list[OverrideResponse])
async def get_disagreements(skip: int = 0, limit: int = 100, service: OverrideService = Depends(get_override_service)):
    return await service.get_disagreements(skip, limit)


@router.get("/invoice/{invoice_id}", response_model=list[OverrideResponse])
async def get_by_invoice(invoice_id: UUID, service: OverrideService = Depends(get_override_service)):
    return await service.get_by_invoice_id(invoice_id)


@router.get("/vendor/{vendor_id}", response_model=list[OverrideResponse])
async def get_by_vendor(vendor_id: UUID, service: OverrideService = Depends(get_override_service)):
    return await service.get_by_vendor_id(vendor_id)


@router.get("/{id}", response_model=OverrideResponse)
async def get_one(id: UUID, service: OverrideService = Depends(get_override_service)):
    override = await service.get_override(id)
    if not override:
        raise HTTPException(status_code=404, detail="Override not found")
    return override


@router.post("/", response_model=OverrideResponse, status_code=201)
async def create(data: OverrideCreate, service: OverrideService = Depends(get_override_service)):
    return await service.create_override(data)


@router.patch("/{id}", response_model=OverrideResponse)
async def update(id: UUID, data: OverrideUpdate, service: OverrideService = Depends(get_override_service)):
    override = await service.update_override(id, data)
    if not override:
        raise HTTPException(status_code=404, detail="Override not found")
    return override


@router.delete("/{id}", status_code=204)
async def delete(id: UUID, service: OverrideService = Depends(get_override_service)):
    if not await service.delete_override(id):
        raise HTTPException(status_code=404, detail="Override not found")
