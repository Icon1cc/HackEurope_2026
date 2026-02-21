import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routers import router
from app.core.database import init_db, close_db
from app.core.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("Database initialized")
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

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Welcome to HackEurope 2026 API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
