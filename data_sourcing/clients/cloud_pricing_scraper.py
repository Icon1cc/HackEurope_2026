"""
Scrape on-demand compute pricing from cloudprice.net for AWS, GCP, and Azure.
Outputs structured JSON ready for DB ingestion.

Usage:
    uv run -m clients.cloud_pricing_scraper
    uv run -m clients.cloud_pricing_scraper --out data/cloud_pricing.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

SOURCES = {
    "aws": "https://cloudprice.net/aws/ec2",
    "gcp": "https://cloudprice.net/gcp/compute",
    "azure": "https://cloudprice.net/",
}

# Columns returned by each provider's table (after stripping checkbox col[0])
# Identified empirically from live scrape on 2026-02-21.
AWS_COLS   = ["instance_type", "family", "vcpus", "memory_gib", "arch", "gpu", "price_usd_hr", "_find_better", "_compare", "best_region"]
GCP_COLS   = ["instance_type", "family", "vcpus", "memory_gib", "price_usd_hr", "_find_better", "_compare", "best_region"]
AZURE_COLS = ["instance_type", "vcpus", "memory_gib", "linux_price_usd_hr", "windows_price_usd_hr", "_find_better", "_compare", "best_region"]


def _wait_for_table(page) -> None:
    page.wait_for_selector("table tbody tr", timeout=15_000)
    page.wait_for_timeout(1_500)  # let JS finish populating


def _scrape_rows(page) -> list[list[str]]:
    return page.evaluate("""() =>
        [...document.querySelectorAll('table tbody tr')].map(tr =>
            [...tr.querySelectorAll('td')].map(td => td.innerText.trim())
        )
    """)


def _map_row(raw: list[str], col_names: list[str]) -> dict:
    """Map raw cell list → named dict, skipping private cols (prefixed _)."""
    # col[0] is always an empty checkbox cell — drop it
    cells = raw[1:]
    record = {}
    for i, name in enumerate(col_names):
        if name.startswith("_"):
            continue
        record[name] = cells[i] if i < len(cells) else None
    return record


def _coerce_numerics(record: dict, numeric_fields: list[str]) -> dict:
    for field in numeric_fields:
        val = record.get(field)
        if val is not None:
            try:
                record[field] = float(val)
            except (ValueError, TypeError):
                record[field] = None
    return record


def scrape_aws(page) -> list[dict]:
    page.goto(SOURCES["aws"])
    _wait_for_table(page)
    rows = _scrape_rows(page)
    records = []
    for raw in rows:
        if not raw or raw[0] == "No matching records found":
            continue
        r = _map_row(raw, AWS_COLS)
        r["gpu"] = r.get("gpu", "no").lower() == "yes"
        r = _coerce_numerics(r, ["vcpus", "memory_gib", "price_usd_hr"])
        r["provider"] = "aws"
        records.append(r)
    return records


def scrape_gcp(page) -> list[dict]:
    page.goto(SOURCES["gcp"])
    _wait_for_table(page)
    rows = _scrape_rows(page)
    records = []
    for raw in rows:
        if not raw or raw[0] == "No matching records found":
            continue
        r = _map_row(raw, GCP_COLS)
        r = _coerce_numerics(r, ["vcpus", "memory_gib", "price_usd_hr"])
        r["provider"] = "gcp"
        records.append(r)
    return records


def scrape_azure(page) -> list[dict]:
    page.goto(SOURCES["azure"])
    _wait_for_table(page)
    rows = _scrape_rows(page)
    records = []
    for raw in rows:
        if not raw or raw[0] == "No matching records found":
            continue
        r = _map_row(raw, AZURE_COLS)
        r = _coerce_numerics(r, ["vcpus", "memory_gib", "linux_price_usd_hr", "windows_price_usd_hr"])
        # Normalise: use linux price as canonical price_usd_hr
        r["price_usd_hr"] = r.get("linux_price_usd_hr")
        r["provider"] = "azure"
        records.append(r)
    return records


def scrape_all(headless: bool = True) -> dict:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        try:
            print("Scraping AWS EC2...")
            aws = scrape_aws(page)
            print(f"  {len(aws)} instances")

            print("Scraping GCP Compute...")
            gcp = scrape_gcp(page)
            print(f"  {len(gcp)} instances")

            print("Scraping Azure VMs...")
            azure = scrape_azure(page)
            print(f"  {len(azure)} instances")
        finally:
            browser.close()

    return {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "source": "cloudprice.net",
        "pricing_type": "on_demand",
        "currency": "USD",
        "records": aws + gcp + azure,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/cloud_pricing.json", help="Output JSON path")
    parser.add_argument("--no-headless", action="store_true", help="Show browser window")
    args = parser.parse_args()

    data = scrape_all(headless=not args.no_headless)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2))
    print(f"\nSaved {len(data['records'])} records -> {out}")


if __name__ == "__main__":
    main()
