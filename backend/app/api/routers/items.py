from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.services.item import ItemService
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.core.dependencies import get_item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=list[ItemResponse])
async def get_all(skip: int = 0, limit: int = 100, service: ItemService = Depends(get_item_service)):
    return await service.get_all_items(skip, limit)


@router.get("/invoice/{invoice_id}", response_model=list[ItemResponse])
async def get_by_invoice(invoice_id: UUID, skip: int = 0, limit: int = 100, service: ItemService = Depends(get_item_service)):
    return await service.get_by_invoice_id(invoice_id, skip, limit)


@router.get("/{id}", response_model=ItemResponse)
async def get_one(id: UUID, service: ItemService = Depends(get_item_service)):
    item = await service.get_item(id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/", response_model=ItemResponse, status_code=201)
async def create(data: ItemCreate, service: ItemService = Depends(get_item_service)):
    return await service.create_item(data)


@router.patch("/{id}", response_model=ItemResponse)
async def update(id: UUID, data: ItemUpdate, service: ItemService = Depends(get_item_service)):
    item = await service.update_item(id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.delete("/{id}", status_code=204)
async def delete(id: UUID, service: ItemService = Depends(get_item_service)):
    if not await service.delete_item(id):
        raise HTTPException(status_code=404, detail="Item not found")
