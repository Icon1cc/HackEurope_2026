import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import router
from app.core.database import init_db, close_db
from app.core.config import get_settings
from app.core.stripe_client import init_stripe

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        init_stripe()
        logger.info("Database and Stripe initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    try:
        yield
    finally:
        try:
            await close_db()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)


def _get_cors_origins() -> list[str]:
    raw_origins = os.getenv("BACKEND_CORS_ORIGINS")
    if raw_origins:
        parsed = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
        if parsed:
            return parsed
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Welcome to HackEurope 2026 API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
