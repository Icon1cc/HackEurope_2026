from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from app.services.market_data import MarketDataService
from app.schemas.market_data import MarketDataCreate, MarketDataUpdate, MarketDataResponse
from app.core.dependencies import get_market_data_service, get_current_user

router = APIRouter(prefix="/market-data", tags=["market_data"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=list[MarketDataResponse])
async def get_all(skip: int = 0, limit: int = 100, service: MarketDataService = Depends(get_market_data_service)):
    return await service.get_all_market_data(skip, limit)


@router.get("/category/{category}", response_model=list[MarketDataResponse])
async def get_by_category(category: str, skip: int = 0, limit: int = 100, service: MarketDataService = Depends(get_market_data_service)):
    return await service.get_by_category(category, skip, limit)


@router.get("/{id}", response_model=MarketDataResponse)
async def get_one(id: UUID, service: MarketDataService = Depends(get_market_data_service)):
    data = await service.get_market_data(id)
    if not data:
        raise HTTPException(status_code=404, detail="Market data not found")
    return data


@router.post("/", response_model=MarketDataResponse, status_code=201)
async def create(data: MarketDataCreate, service: MarketDataService = Depends(get_market_data_service)):
    return await service.create_market_data(data)


@router.patch("/{id}", response_model=MarketDataResponse)
async def update(id: UUID, data: MarketDataUpdate, service: MarketDataService = Depends(get_market_data_service)):
    entry = await service.update_market_data(id, data)
    if not entry:
        raise HTTPException(status_code=404, detail="Market data not found")
    return entry


@router.delete("/{id}", status_code=204)
async def delete(id: UUID, service: MarketDataService = Depends(get_market_data_service)):
    if not await service.delete_market_data(id):
        raise HTTPException(status_code=404, detail="Market data not found")
