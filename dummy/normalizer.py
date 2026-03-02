"""
pricing/normalizer.py

Converts raw API records (as returned by the fetcher) into a list of
unified dicts ready to be upserted into the cloud_pricing table.

Each normalizer function receives the full parsed JSON payload saved by
the fetcher and returns List[dict] where every dict maps 1-to-1 with the
CloudPricing model columns.

Hourly-unit detection
─────────────────────
If the raw unit indicates an hourly charge (Hrs / Hour / h / hour) we
copy price_per_unit directly into price_per_hour.
For non-hourly SKUs (GB, Requests, Lambda-GB-Second, Objects …) we set
price_per_hour = None — the invoice checker uses that field to decide
whether a SKU is eligible for hourly comparison.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional


# ── helpers ────────────────────────────────────────────────────────────────
_HOURLY_UNITS = {"hrs", "hour", "h", "1 hour"}


def _to_decimal(value: Any) -> Optional[Decimal]:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def _is_hourly(unit: str) -> bool:
    return unit.strip().lower() in _HOURLY_UNITS


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value[:19], fmt[:len(value[:19])])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass
    return None


def _category_from_service(service_name: str) -> str:
    s = service_name.lower()
    if any(k in s for k in ("ec2", "compute engine", "virtual machine", "kubernetes")):
        return "Compute"
    if any(k in s for k in ("s3", "storage", "blob")):
        return "Storage"
    if any(k in s for k in ("rds", "cloud sql", "database", "aurora")):
        return "Database"
    if any(k in s for k in ("cloudfront", "cdn")):
        return "CDN"
    return "Other"


# ── 1. Infracost GraphQL (AWS EC2 + Azure VMs) ────────────────────────────
def normalize_infracost(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        attrs: Dict[str, str] = {
            a["key"]: a["value"] for a in raw.get("attributes", [])
        }
        vendor      = raw.get("vendorName", "unknown").lower()
        service     = raw.get("service", "Unknown")
        region      = raw.get("region", "")
        sku_id      = attrs.get("meterId") or attrs.get("skuName", "")
        description = attrs.get("productName") or attrs.get("skuName", "")

        prices = raw.get("prices", [])
        if not prices:
            # No price data — still store with price 0 so the SKU is catalogued
            records.append({
                "vendor":           vendor,
                "service_name":     service,
                "category":         _category_from_service(service),
                "sku_id":           sku_id,
                "description":      description,
                "region":           region,
                "instance_type":    attrs.get("armSkuName") or None,
                "operating_system": None,
                "price_per_unit":   Decimal("0"),
                "unit":             "Hrs",
                "price_per_hour":   Decimal("0"),
                "currency":         "USD",
                "effective_date":   _parse_dt(attrs.get("effectiveStartDate")),
                "raw_attributes":   raw,
                "source_api":       "infracost",
            })
            continue

        for price in prices:
            ppu = _to_decimal(price.get("USD", 0))
            if ppu is None:
                continue
            unit = price.get("unit", "Hrs")
            records.append({
                "vendor":           vendor,
                "service_name":     service,
                "category":         _category_from_service(service),
                "sku_id":           sku_id,
                "description":      price.get("description") or description,
                "region":           region,
                "instance_type":    attrs.get("armSkuName") or None,
                "operating_system": None,
                "price_per_unit":   ppu,
                "unit":             unit,
                "price_per_hour":   ppu if _is_hourly(unit) else None,
                "currency":         "USD",
                "effective_date":   _parse_dt(
                    price.get("effectiveDateStart") or attrs.get("effectiveStartDate")
                ),
                "raw_attributes":   raw,
                "source_api":       "infracost",
            })
    return records


# ── 2. AWS EC2 CSV ─────────────────────────────────────────────────────────
def normalize_aws_ec2(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("PricePerUnit", 0))
        if ppu is None:
            continue
        unit = raw.get("Unit", "Hrs")
        records.append({
            "vendor":           "aws",
            "service_name":     raw.get("serviceName", "Amazon EC2"),
            "category":         "Compute",
            "sku_id":           raw.get("SKU", ""),
            "description":      raw.get("PriceDescription", ""),
            "region":           raw.get("Region Code", raw.get("Location", "")),
            "instance_type":    raw.get("Instance Type") or None,
            "operating_system": raw.get("Operating System") or None,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   ppu if _is_hourly(unit) else None,
            "currency":         raw.get("Currency", "USD"),
            "effective_date":   _parse_dt(raw.get("EffectiveDate")),
            "raw_attributes":   raw,
            "source_api":       "aws_ec2",
        })
    return records


# ── 3. AWS S3 CSV ──────────────────────────────────────────────────────────
def normalize_aws_s3(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("PricePerUnit", 0))
        if ppu is None:
            continue
        unit = raw.get("Unit", "GB")
        records.append({
            "vendor":           "aws",
            "service_name":     raw.get("serviceName", "Amazon S3"),
            "category":         "Storage",
            "sku_id":           raw.get("SKU", ""),
            "description":      raw.get("PriceDescription", ""),
            "region":           raw.get("Region Code", ""),
            "instance_type":    None,
            "operating_system": None,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   ppu if _is_hourly(unit) else None,
            "currency":         raw.get("Currency", "USD"),
            "effective_date":   _parse_dt(raw.get("EffectiveDate")),
            "raw_attributes":   raw,
            "source_api":       "aws_s3",
        })
    return records


# ── 4. AWS RDS CSV ─────────────────────────────────────────────────────────
def normalize_aws_rds(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("PricePerUnit", 0))
        if ppu is None:
            continue
        unit = raw.get("Unit", "Hrs")
        db_engine = raw.get("Database Engine", "")
        desc      = raw.get("PriceDescription", "")
        records.append({
            "vendor":           "aws",
            "service_name":     raw.get("serviceName", "Amazon RDS"),
            "category":         "Database",
            "sku_id":           raw.get("SKU", ""),
            "description":      desc,
            "region":           raw.get("Region Code", ""),
            "instance_type":    raw.get("Instance Type") or None,
            "operating_system": db_engine or None,   # repurposed for DB engine
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   ppu if _is_hourly(unit) else None,
            "currency":         raw.get("Currency", "USD"),
            "effective_date":   _parse_dt(raw.get("EffectiveDate")),
            "raw_attributes":   raw,
            "source_api":       "aws_rds",
        })
    return records


# ── 5. AWS CloudFront CSV ──────────────────────────────────────────────────
def normalize_aws_cloudfront(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("PricePerUnit", 0))
        if ppu is None:
            continue
        unit = raw.get("Unit", "GB")
        records.append({
            "vendor":           "aws",
            "service_name":     raw.get("serviceName", "Amazon CloudFront"),
            "category":         "CDN",
            "sku_id":           raw.get("SKU", ""),
            "description":      raw.get("PriceDescription", ""),
            "region":           raw.get("Region Code") or raw.get("From Region Code", ""),
            "instance_type":    None,
            "operating_system": None,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   ppu if _is_hourly(unit) else None,
            "currency":         raw.get("Currency", "USD"),
            "effective_date":   _parse_dt(raw.get("EffectiveDate")),
            "raw_attributes":   raw,
            "source_api":       "aws_cloudfront",
        })
    return records


# ── 6. Azure Retail Prices API ─────────────────────────────────────────────
def normalize_azure(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("retailPrice", raw.get("unitPrice", 0)))
        if ppu is None:
            continue
        unit     = raw.get("unitOfMeasure", "1 Hour")
        service  = raw.get("serviceName", "Unknown")
        prod     = raw.get("productName", "")
        sku_name = raw.get("skuName", "")
        desc     = f"{prod} – {sku_name}".strip(" –")

        records.append({
            "vendor":           "azure",
            "service_name":     service,
            "category":         _category_from_service(service),
            "sku_id":           raw.get("skuId") or raw.get("meterId", ""),
            "description":      desc,
            "region":           raw.get("armRegionName", ""),
            "instance_type":    raw.get("armSkuName") or sku_name or None,
            "operating_system": None,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   ppu if _is_hourly(unit) else None,
            "currency":         raw.get("currencyCode", "USD"),
            "effective_date":   _parse_dt(raw.get("effectiveStartDate")),
            "raw_attributes":   raw,
            "source_api":       "azure",
        })
    return records


# ── 7. GCP Cloud Billing Catalog ───────────────────────────────────────────
def normalize_gcp(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("priceUSD", 0))
        if ppu is None:
            continue
        unit    = raw.get("usageUnit", "h")
        service = raw.get("service", "Compute Engine")
        cat     = raw.get("category", {})
        regions = raw.get("serviceRegions", [])
        region  = regions[0] if regions else ""

        records.append({
            "vendor":           "gcp",
            "service_name":     service,
            "category":         _category_from_service(service),
            "sku_id":           raw.get("skuId", ""),
            "description":      raw.get("description", ""),
            "region":           region,
            "instance_type":    None,
            "operating_system": None,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   ppu if _is_hourly(unit) else None,
            "currency":         raw.get("currencyCode", "USD"),
            "effective_date":   _parse_dt(raw.get("effectiveTime")),
            "raw_attributes":   raw,
            "source_api":       "gcp",
        })
    return records


# ── Master dispatcher ──────────────────────────────────────────────────────
SOURCE_NORMALIZERS = {
    "infracost":       normalize_infracost,
    "aws_ec2":         normalize_aws_ec2,
    "aws_s3":          normalize_aws_s3,
    "aws_rds":         normalize_aws_rds,
    "aws_cloudfront":  normalize_aws_cloudfront,
    "azure":           normalize_azure,
    "gcp":             normalize_gcp,
}


def normalize_all(payloads: Dict[str, Dict]) -> List[dict]:
    """
    Given a dict of { source_name: raw_payload }, return a flat list of
    normalised pricing records.

    Example
    -------
    payloads = {
        "aws_ec2":   { ... },
        "aws_s3":    { ... },
        "azure":     { ... },
        "gcp":       { ... },
    }
    records = normalize_all(payloads)
    """
    all_records: List[dict] = []
    for source, payload in payloads.items():
        fn = SOURCE_NORMALIZERS.get(source)
        if fn is None:
            continue
        if payload.get("status") in ("skipped", "error"):
            continue
        normalised = fn(payload)
        all_records.extend(normalised)

    return all_records
