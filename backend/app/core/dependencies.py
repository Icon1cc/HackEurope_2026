from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.invoice import InvoiceRepository
from app.repositories.vendor import VendorRepository
from app.repositories.payment import PaymentRepository
from app.repositories.override import OverrideRepository
from app.repositories.client import ClientRepository
from app.repositories.market_data import MarketDataRepository
from app.repositories.item import ItemRepository
from app.repositories.cloud_pricing import CloudPricingRepository
from app.services.invoice import InvoiceService
from app.services.vendor import VendorService
from app.services.payment import PaymentService
from app.services.override import OverrideService
from app.services.client import ClientService
from app.services.market_data import MarketDataService
from app.services.item import ItemService
from app.services.cloud_pricing import CloudPricingService


# --- Repositories ---

def get_invoice_repo(db: AsyncSession = Depends(get_db)) -> InvoiceRepository:
    return InvoiceRepository(db)

def get_vendor_repo(db: AsyncSession = Depends(get_db)) -> VendorRepository:
    return VendorRepository(db)

def get_payment_repo(db: AsyncSession = Depends(get_db)) -> PaymentRepository:
    return PaymentRepository(db)

def get_override_repo(db: AsyncSession = Depends(get_db)) -> OverrideRepository:
    return OverrideRepository(db)

def get_client_repo(db: AsyncSession = Depends(get_db)) -> ClientRepository:
    return ClientRepository(db)

def get_market_data_repo(db: AsyncSession = Depends(get_db)) -> MarketDataRepository:
    return MarketDataRepository(db)

def get_item_repo(db: AsyncSession = Depends(get_db)) -> ItemRepository:
    return ItemRepository(db)

def get_cloud_pricing_repo(db: AsyncSession = Depends(get_db)) -> CloudPricingRepository:
    return CloudPricingRepository(db)


# --- Services ---

def get_invoice_service(repo: InvoiceRepository = Depends(get_invoice_repo)) -> InvoiceService:
    return InvoiceService(repo)

def get_vendor_service(repo: VendorRepository = Depends(get_vendor_repo)) -> VendorService:
    return VendorService(repo)

def get_payment_service(repo: PaymentRepository = Depends(get_payment_repo)) -> PaymentService:
    return PaymentService(repo)

def get_override_service(repo: OverrideRepository = Depends(get_override_repo)) -> OverrideService:
    return OverrideService(repo)

def get_client_service(repo: ClientRepository = Depends(get_client_repo)) -> ClientService:
    return ClientService(repo)

def get_market_data_service(repo: MarketDataRepository = Depends(get_market_data_repo)) -> MarketDataService:
    return MarketDataService(repo)

def get_item_service(repo: ItemRepository = Depends(get_item_repo)) -> ItemService:
    return ItemService(repo)

def get_cloud_pricing_service(
    repo: CloudPricingRepository = Depends(get_cloud_pricing_repo),
    market_data_repo: MarketDataRepository = Depends(get_market_data_repo),
) -> CloudPricingService:
    return CloudPricingService(repo, market_data_repo=market_data_repo)
