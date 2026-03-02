"""
worker.py
Standalone pricing sync worker — runs independently of the FastAPI server.

Schedule: every 12 hours (configurable via SYNC_INTERVAL_HOURS env var).

Run with:
  python worker.py

The worker uses APScheduler and shares the same SQLAlchemy engine as the
API, but runs in its own process so it can't block request handling.

Deployment options
──────────────────
  Local / dev   : python worker.py  (keep terminal open or use screen/tmux)
  Docker        : add a second container in docker-compose.yml (see README)
  Systemd       : create a .service unit that ExecStart=python worker.py
  Kubernetes    : deploy as a separate Deployment or CronJob
"""

import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv

load_dotenv()

# ── logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger("invoiceguard.worker")

# ── config ─────────────────────────────────────────────────────────────────
SYNC_INTERVAL_HOURS = float(os.getenv("SYNC_INTERVAL_HOURS", "12"))

# ── import shared modules ─────────────────────────────────────────────────
# Ensure the project root is on sys.path when worker.py is run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, init_db          # noqa: E402
from pricing.fetcher import fetch_all               # noqa: E402
from pricing.normalizer import normalize_all        # noqa: E402
from pricing.service import upsert_pricing_records  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Core sync job
# ─────────────────────────────────────────────────────────────────────────────

def run_sync() -> None:
    """
    Fetch all cloud pricing APIs → normalise → upsert into PostgreSQL.
    Any exception is caught so the scheduler continues running.
    """
    start = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info("Pricing sync started at %s", start.isoformat())
    logger.info("=" * 60)

    try:
        # 1. Fetch raw data from all sources
        payloads = fetch_all()

        source_summary = {
            src: payload.get("records_saved", payload.get("total_records", payload.get("status", "?")))
            for src, payload in payloads.items()
        }
        logger.info("Fetch complete: %s", source_summary)

        # 2. Normalise into unified records
        records = normalize_all(payloads)
        logger.info("Normalised: %d total records", len(records))

        if not records:
            logger.warning("No records to upsert — all APIs may have failed or been skipped")
            return

        # 3. Upsert into PostgreSQL
        db = SessionLocal()
        try:
            affected, _ = upsert_pricing_records(db, records)
            logger.info("Upserted %d rows into cloud_pricing", affected)
        finally:
            db.close()

        elapsed = (datetime.now(timezone.utc) - start).total_seconds()
        logger.info("Sync finished in %.1fs ✓", elapsed)

    except Exception:
        logger.exception("Pricing sync failed — will retry at next scheduled interval")


# ─────────────────────────────────────────────────────────────────────────────
# Scheduler setup
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("InvoiceGuard Pricing Worker starting …")
    logger.info("Sync interval: every %.1f hours", SYNC_INTERVAL_HOURS)

    # Ensure tables exist (idempotent)
    init_db()
    logger.info("Database tables verified ✓")

    # Run immediately on startup so you don't wait up to 12 hours after deploy
    logger.info("Running initial sync on startup …")
    run_sync()

    # Schedule recurring syncs
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_sync,
        trigger=IntervalTrigger(hours=SYNC_INTERVAL_HOURS),
        id="pricing_sync",
        name="Cloud Pricing Full Sync",
        max_instances=1,          # prevent overlapping runs
        coalesce=True,            # if two runs are due, fire only once
        misfire_grace_time=300,   # allow 5-minute slippage before skipping
    )

    # Graceful shutdown on SIGINT / SIGTERM
    def _shutdown(sig, frame):
        logger.info("Shutdown signal received — stopping scheduler …")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT,  _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(
        "Scheduler running — next sync at %s",
        scheduler.get_jobs()[0].next_run_time if scheduler.get_jobs() else "unknown",
    )
    scheduler.start()


if __name__ == "__main__":
    main()
