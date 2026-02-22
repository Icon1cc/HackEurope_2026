from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.services.invoice import InvoiceService
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.core.dependencies import get_invoice_service, get_current_user

router = APIRouter(prefix="/invoices", tags=["invoices"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[InvoiceResponse])
async def get_all(skip: int = 0, limit: int = 100, service: InvoiceService = Depends(get_invoice_service)):
    return await service.get_all_invoices(skip, limit)


@router.get("/flagged", response_model=list[InvoiceResponse])
async def get_flagged(skip: int = 0, limit: int = 100, service: InvoiceService = Depends(get_invoice_service)):
    return await service.get_flagged(skip, limit)


@router.get("/status/{status}", response_model=list[InvoiceResponse])
async def get_by_status(status: str, skip: int = 0, limit: int = 100, service: InvoiceService = Depends(get_invoice_service)):
    return await service.get_by_status(status, skip, limit)


@router.get("/{id}", response_model=InvoiceResponse)
async def get_one(id: UUID, service: InvoiceService = Depends(get_invoice_service)):
    invoice = await service.get_invoice(id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/", response_model=InvoiceResponse, status_code=201)
async def create(data: InvoiceCreate, service: InvoiceService = Depends(get_invoice_service)):
    return await service.create_invoice(data)


@router.patch("/{id}", response_model=InvoiceResponse)
async def update(id: UUID, data: InvoiceUpdate, service: InvoiceService = Depends(get_invoice_service)):
    invoice = await service.update_invoice(id, data)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.delete("/{id}", status_code=204)
async def delete(id: UUID, service: InvoiceService = Depends(get_invoice_service)):
    if not await service.delete_invoice(id):
        raise HTTPException(status_code=404, detail="Invoice not found")
