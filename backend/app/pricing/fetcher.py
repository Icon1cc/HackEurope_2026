"""
Fetches raw pricing data from cloud provider APIs.
Returns a dict keyed by source name, ready for normalize_all().

Runs synchronous HTTP calls — use asyncio.to_thread(fetch_all)
from async code.

REQUIRED ENV VARS:
  INFRACOST_API_KEY  – from: infracost auth login
  GCP_API_KEY        – Google Cloud Billing API key
"""

from __future__ import annotations

import csv
import io
import logging
import os
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

_TIMEOUT_SHORT = 15
_TIMEOUT_LONG = 90

INFRACOST_KEY = os.getenv("INFRACOST_API_KEY", "")
GCP_KEY = (
    os.getenv("GCP_API_KEY", "")
    or os.getenv("GOOGLE_API_KEY", "")
    or os.getenv("GOOGLE_CLOUD_API_KEY", "")
)

MAX_RECORDS = int(os.getenv("PRICING_MAX_RECORDS", "5"))


# ── helpers ───────────────────────────────────────────────────────────────

def _stream_aws_csv(url: str, max_lines: int = 60_000) -> Tuple[List[str], List[Dict]]:
    resp = requests.get(url, stream=True, timeout=_TIMEOUT_LONG)
    resp.raise_for_status()

    raw_lines: List[str] = []
    for raw in resp.iter_lines():
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        raw_lines.append(line)
        if len(raw_lines) >= max_lines:
            break

    header_idx: Optional[int] = None
    for i, line in enumerate(raw_lines):
        try:
            first = next(csv.reader(io.StringIO(line)))
        except StopIteration:
            continue
        if first and first[0] == "SKU":
            header_idx = i
            break

    if header_idx is None:
        return [], []

    headers = next(csv.reader(io.StringIO(raw_lines[header_idx])))
    rows: List[Dict] = []
    for raw_row in raw_lines[header_idx + 1:]:
        if not raw_row.strip():
            continue
        try:
            cells = next(csv.reader(io.StringIO(raw_row)))
        except StopIteration:
            continue
        if len(cells) >= len(headers):
            rows.append(dict(zip(headers, cells[:len(headers)])))

    return headers, rows


# ── 1. Infracost GraphQL ─────────────────────────────────────────────────

def fetch_infracost() -> Dict:
    if not INFRACOST_KEY:
        logger.warning("INFRACOST_API_KEY not set — skipping")
        return {"status": "skipped", "reason": "INFRACOST_API_KEY not set"}

    endpoint = "https://pricing.api.infracost.io/graphql"
    queries = [
        {
            "label": "AWS EC2 Linux OnDemand (us-east-1)",
            "query": """{
                products(filter: {
                    vendorName: "aws", service: "AmazonEC2",
                    productFamily: "Compute Instance", region: "us-east-1",
                    attributeFilters: [
                        {key: "operatingSystem", value: "Linux"},
                        {key: "tenancy", value: "Shared"},
                        {key: "capacitystatus", value: "Used"},
                        {key: "preInstalledSw", value: "NA"}
                    ]
                }) {
                    vendorName service productFamily region
                    attributes { key value }
                    prices(filter: {purchaseOption: "on_demand"}) {
                        USD unit description effectiveDateStart
                    }
                }
            }""",
        },
        {
            "label": "AWS EC2 Linux OnDemand (eu-west-1)",
            "query": """{
                products(filter: {
                    vendorName: "aws", service: "AmazonEC2",
                    productFamily: "Compute Instance", region: "eu-west-1",
                    attributeFilters: [
                        {key: "operatingSystem", value: "Linux"},
                        {key: "tenancy", value: "Shared"},
                        {key: "capacitystatus", value: "Used"},
                        {key: "preInstalledSw", value: "NA"}
                    ]
                }) {
                    vendorName service productFamily region
                    attributes { key value }
                    prices(filter: {purchaseOption: "on_demand"}) {
                        USD unit description effectiveDateStart
                    }
                }
            }""",
        },
        {
            "label": "Azure VMs (westus)",
            "query": """{
                products(filter: {
                    vendorName: "azure", service: "Virtual Machines", region: "westus"
                }) {
                    vendorName service productFamily region
                    attributes { key value }
                    prices(filter: {purchaseOption: "Consumption"}) {
                        USD unit description effectiveDateStart
                    }
                }
            }""",
        },
    ]

    all_products = []
    for q in queries:
        try:
            resp = requests.post(
                endpoint,
                headers={"X-Api-Key": INFRACOST_KEY, "Content-Type": "application/json"},
                json={"query": q["query"]},
                timeout=_TIMEOUT_SHORT,
            )
            resp.raise_for_status()
            body = resp.json()
            if body.get("errors"):
                logger.error("Infracost GraphQL errors: %s", body["errors"])
                continue
            products = (body.get("data") or {}).get("products") or []
            for p in products:
                p["_query_label"] = q["label"]
            all_products.extend(products)
            logger.info("Infracost [%s] → %d products", q["label"], len(products))
        except Exception as exc:
            logger.exception("Infracost query failed for %s: %s", q["label"], exc)

    all_products = all_products[:MAX_RECORDS]
    return {
        "api": "Infracost GraphQL",
        "endpoint": endpoint,
        "total_records": len(all_products),
        "records_saved": len(all_products),
        "raw_records": all_products,
    }


# ── 2. AWS EC2 ───────────────────────────────────────────────────────────

def fetch_aws_ec2() -> Dict:
    url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/eu-west-1/index.csv"
    try:
        headers, all_rows = _stream_aws_csv(url)
        rows = [
            r for r in all_rows
            if r.get("TermType") == "OnDemand"
            and r.get("Operating System") == "Linux"
            and r.get("Tenancy") == "Shared"
            and r.get("Unit") == "Hrs"
            and r.get("PricePerUnit", "") not in ("", "0", "0.0000000000")
        ][:MAX_RECORDS]
        logger.info("AWS EC2 → %d OnDemand Linux rows (of %d total)", len(rows), len(all_rows))
        return {
            "api": "AWS Price List API",
            "endpoint": url,
            "csv_columns": headers,
            "records_saved": len(rows),
            "raw_records": rows,
        }
    except Exception as exc:
        logger.exception("AWS EC2 fetch failed: %s", exc)
        return {"status": "error", "error": str(exc)}


# ── 3. AWS S3 ────────────────────────────────────────────────────────────

def fetch_aws_s3() -> Dict:
    url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/eu-west-1/index.csv"
    try:
        headers, all_rows = _stream_aws_csv(url, max_lines=20_000)
        rows = [
            r for r in all_rows
            if r.get("PricePerUnit", "") not in ("", "0", "0.0000000000")
        ][:MAX_RECORDS]
        logger.info("AWS S3 → %d rows with non-zero price", len(rows))
        return {
            "api": "AWS Price List API",
            "endpoint": url,
            "csv_columns": headers,
            "records_saved": len(rows),
            "raw_records": rows,
        }
    except Exception as exc:
        logger.exception("AWS S3 fetch failed: %s", exc)
        return {"status": "error", "error": str(exc)}


# ── 4. AWS RDS ───────────────────────────────────────────────────────────

def fetch_aws_rds() -> Dict:
    url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/eu-west-1/index.csv"
    try:
        headers, all_rows = _stream_aws_csv(url)
        rows = [
            r for r in all_rows
            if r.get("TermType") == "OnDemand"
            and r.get("PricePerUnit", "") not in ("", "0", "0.0000000000")
            and r.get("Unit") == "Hrs"
        ][:MAX_RECORDS]
        logger.info("AWS RDS → %d OnDemand hourly rows", len(rows))
        return {
            "api": "AWS Price List API",
            "endpoint": url,
            "csv_columns": headers,
            "records_saved": len(rows),
            "raw_records": rows,
        }
    except Exception as exc:
        logger.exception("AWS RDS fetch failed: %s", exc)
        return {"status": "error", "error": str(exc)}


# ── 5. AWS CloudFront ────────────────────────────────────────────────────

def fetch_aws_cloudfront() -> Dict:
    url = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonCloudFront/current/index.csv"
    try:
        headers, all_rows = _stream_aws_csv(url, max_lines=20_000)
        rows = [
            r for r in all_rows
            if r.get("PricePerUnit", "") not in ("", "0", "0.0000000000")
        ][:MAX_RECORDS]
        logger.info("AWS CloudFront → %d rows with non-zero price", len(rows))
        return {
            "api": "AWS Price List API",
            "endpoint": url,
            "csv_columns": headers,
            "records_saved": len(rows),
            "raw_records": rows,
        }
    except Exception as exc:
        logger.exception("AWS CloudFront fetch failed: %s", exc)
        return {"status": "error", "error": str(exc)}


# ── 6. Azure Retail Prices ───────────────────────────────────────────────

def fetch_azure() -> Dict:
    all_items = []
    url: Optional[str] = "https://prices.azure.com/api/retail/prices"
    params = {
        "api-version": "2021-10-01-preview",
        "$filter": "armRegionName eq 'westeurope' and priceType eq 'Consumption'",
    }
    try:
        while url and len(all_items) < MAX_RECORDS:
            resp = requests.get(url, params=params, timeout=_TIMEOUT_SHORT)
            resp.raise_for_status()
            data = resp.json()
            all_items.extend(data.get("Items", []))
            url = data.get("NextPageLink")
            params = None
            logger.info("Azure → %d records so far", len(all_items))
        all_items = all_items[:MAX_RECORDS]
        return {
            "api": "Azure Retail Prices API",
            "endpoint": "https://prices.azure.com/api/retail/prices",
            "records_saved": len(all_items),
            "raw_records": all_items,
        }
    except Exception as exc:
        logger.exception("Azure fetch failed: %s", exc)
        return {"status": "error", "error": str(exc)}


# ── 7. GCP Cloud Billing Catalog ─────────────────────────────────────────

def fetch_gcp() -> Dict:
    if not GCP_KEY:
        logger.warning("GCP API key not set — skipping")
        return {"status": "skipped", "reason": "GCP API key not set"}

    gcp_services = {
        "6F81-5844-456A": "Compute Engine",
        "95FF-2EF5-5EA1": "Cloud Storage",
        "9662-B51E-5089": "Cloud SQL",
    }
    all_skus = []

    for svc_id, svc_name in gcp_services.items():
        page_token = None
        try:
            while len(all_skus) < MAX_RECORDS:
                params = {"key": GCP_KEY, "pageSize": 5000}
                if page_token:
                    params["pageToken"] = page_token
                resp = requests.get(
                    f"https://cloudbilling.googleapis.com/v1/services/{svc_id}/skus",
                    params=params,
                    timeout=_TIMEOUT_SHORT,
                )
                resp.raise_for_status()
                data = resp.json()

                for sku in data.get("skus", []):
                    pi = (sku.get("pricingInfo") or [{}])[0]
                    pe = pi.get("pricingExpression", {})
                    tr = pe.get("tieredRates", [{}])
                    up = (tr[0].get("unitPrice", {}) if tr else {})

                    nanos = up.get("nanos", 0) or 0
                    raw_units = up.get("units", "0")
                    try:
                        units_val = int(raw_units) if raw_units else 0
                    except (ValueError, TypeError):
                        units_val = 0
                    price_usd = units_val + (nanos / 1_000_000_000)

                    all_skus.append({
                        "skuId": sku.get("skuId", ""),
                        "name": sku.get("name", ""),
                        "description": sku.get("description", ""),
                        "service": svc_name,
                        "serviceId": svc_id,
                        "category": sku.get("category", {}),
                        "serviceRegions": sku.get("serviceRegions", []),
                        "usageUnit": pe.get("usageUnit", ""),
                        "usageUnitDescription": pe.get("usageUnitDescription", ""),
                        "priceUSD": price_usd,
                        "currencyCode": up.get("currencyCode", "USD"),
                        "effectiveTime": pi.get("effectiveTime", ""),
                        "summary": pi.get("summary", ""),
                    })

                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            logger.info("GCP %s → %d SKUs", svc_name, len(all_skus))
        except Exception as exc:
            logger.exception("GCP fetch failed for %s: %s", svc_name, exc)

    all_skus = all_skus[:MAX_RECORDS]
    return {
        "api": "GCP Cloud Billing Catalog API v1",
        "endpoint": "https://cloudbilling.googleapis.com/v1/services/{serviceId}/skus",
        "services_queried": list(gcp_services.values()),
        "records_saved": len(all_skus),
        "raw_records": all_skus,
    }


# ── Master fetcher ────────────────────────────────────────────────────────

def fetch_all() -> Dict[str, Dict]:
    """Run all fetchers. One failure doesn't abort the rest."""
    fetchers = {
        "infracost": fetch_infracost,
        "aws_ec2": fetch_aws_ec2,
        "aws_s3": fetch_aws_s3,
        "aws_rds": fetch_aws_rds,
        "aws_cloudfront": fetch_aws_cloudfront,
        "azure": fetch_azure,
        "gcp": fetch_gcp,
    }

    results: Dict[str, Dict] = {}
    for name, fn in fetchers.items():
        logger.info("Fetching: %s …", name)
        try:
            results[name] = fn()
        except Exception as exc:
            logger.exception("Unexpected error in %s: %s", name, exc)
            results[name] = {"status": "error", "error": str(exc)}
        logger.info(
            "  %s done — records=%s",
            name,
            results[name].get("records_saved", results[name].get("total_records", "?")),
        )

    return results
