from fastapi import APIRouter
from app.api.routers.invoices import router as invoices_router
from app.api.routers.vendors import router as vendors_router
from app.api.routers.payments import router as payments_router
from app.api.routers.overrides import router as overrides_router
from app.api.routers.clients import router as clients_router
from app.api.routers.market_data import router as market_data_router
from app.api.routers.items import router as items_router
from app.api.routers.pricing import router as pricing_router
from app.api.routers.extraction import router as extraction_router
from app.api.routers.auth import router as auth_router
from app.api.routers.approve import router as approve_router
from app.api.routers.billing import router as billing_router
from app.api.routers.webhooks import router as webhooks_router

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(webhooks_router)
router.include_router(approve_router)
router.include_router(billing_router)
router.include_router(invoices_router)
router.include_router(vendors_router)
router.include_router(payments_router)
router.include_router(overrides_router)
router.include_router(clients_router)
router.include_router(market_data_router)
router.include_router(items_router)
router.include_router(pricing_router)
router.include_router(extraction_router)
