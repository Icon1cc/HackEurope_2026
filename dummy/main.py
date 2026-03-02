"""
main.py
FastAPI application entry point.

Run with:
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from router import router

# ── logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── lifespan (startup / shutdown) ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("InvoiceGuard starting — creating tables if needed …")
    init_db()
    logger.info("DB initialised ✓")
    yield
    logger.info("InvoiceGuard shutting down")


# ── app ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="InvoiceGuard Pricing API",
    description=(
        "Aggregates live pricing from AWS (EC2, S3, RDS, CloudFront), "
        "Azure, and GCP. Provides invoice validation against current rates."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}
