from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.services.client import ClientService
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.core.dependencies import get_client_service

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/", response_model=list[ClientResponse])
async def get_all(skip: int = 0, limit: int = 100, service: ClientService = Depends(get_client_service)):
    return await service.get_all_clients(skip, limit)


@router.get("/{id}", response_model=ClientResponse)
async def get_one(id: UUID, service: ClientService = Depends(get_client_service)):
    client = await service.get_client(id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("/", response_model=ClientResponse, status_code=201)
async def create(data: ClientCreate, service: ClientService = Depends(get_client_service)):
    return await service.create_client(data)


@router.patch("/{id}", response_model=ClientResponse)
async def update(id: UUID, data: ClientUpdate, service: ClientService = Depends(get_client_service)):
    client = await service.update_client(id, data)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/{id}", status_code=204)
async def delete(id: UUID, service: ClientService = Depends(get_client_service)):
    if not await service.delete_client(id):
        raise HTTPException(status_code=404, detail="Client not found")
