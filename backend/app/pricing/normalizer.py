"""
Converts raw API records (from the fetcher) into a list of unified dicts
ready for upsert into the cloud_pricing table.

Hourly-unit detection: if the raw unit indicates an hourly charge (Hrs/Hour/h)
we copy price_per_unit into price_per_hour. For non-hourly SKUs we set
price_per_hour = None.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional


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


def normalize_infracost(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        attrs: Dict[str, str] = {a["key"]: a["value"] for a in raw.get("attributes", [])}
        vendor = raw.get("vendorName", "unknown").lower()
        service = raw.get("service", "Unknown")
        region = raw.get("region", "")
        sku_id = attrs.get("meterId") or attrs.get("skuName", "")
        description = attrs.get("productName") or attrs.get("skuName", "")

        prices = raw.get("prices", [])
        if not prices:
            records.append({
                "vendor": vendor, "service_name": service,
                "category": _category_from_service(service),
                "sku_id": sku_id, "description": description, "region": region,
                "instance_type": attrs.get("armSkuName") or None,
                "operating_system": None, "price_per_unit": Decimal("0"),
                "unit": "Hrs", "price_per_hour": Decimal("0"), "currency": "USD",
                "effective_date": _parse_dt(attrs.get("effectiveStartDate")),
                "raw_attributes": raw, "source_api": "infracost",
            })
            continue

        for price in prices:
            ppu = _to_decimal(price.get("USD", 0))
            if ppu is None:
                continue
            unit = price.get("unit", "Hrs")
            records.append({
                "vendor": vendor, "service_name": service,
                "category": _category_from_service(service),
                "sku_id": sku_id,
                "description": price.get("description") or description,
                "region": region,
                "instance_type": attrs.get("armSkuName") or None,
                "operating_system": None, "price_per_unit": ppu, "unit": unit,
                "price_per_hour": ppu if _is_hourly(unit) else None,
                "currency": "USD",
                "effective_date": _parse_dt(price.get("effectiveDateStart") or attrs.get("effectiveStartDate")),
                "raw_attributes": raw, "source_api": "infracost",
            })
    return records


def normalize_aws_ec2(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("PricePerUnit", 0))
        if ppu is None:
            continue
        unit = raw.get("Unit", "Hrs")
        records.append({
            "vendor": "aws", "service_name": raw.get("serviceName", "Amazon EC2"),
            "category": "Compute", "sku_id": raw.get("SKU", ""),
            "description": raw.get("PriceDescription", ""),
            "region": raw.get("Region Code", raw.get("Location", "")),
            "instance_type": raw.get("Instance Type") or None,
            "operating_system": raw.get("Operating System") or None,
            "price_per_unit": ppu, "unit": unit,
            "price_per_hour": ppu if _is_hourly(unit) else None,
            "currency": raw.get("Currency", "USD"),
            "effective_date": _parse_dt(raw.get("EffectiveDate")),
            "raw_attributes": raw, "source_api": "aws_ec2",
        })
    return records


def normalize_aws_s3(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("PricePerUnit", 0))
        if ppu is None:
            continue
        unit = raw.get("Unit", "GB")
        records.append({
            "vendor": "aws", "service_name": raw.get("serviceName", "Amazon S3"),
            "category": "Storage", "sku_id": raw.get("SKU", ""),
            "description": raw.get("PriceDescription", ""),
            "region": raw.get("Region Code", ""),
            "instance_type": None, "operating_system": None,
            "price_per_unit": ppu, "unit": unit,
            "price_per_hour": ppu if _is_hourly(unit) else None,
            "currency": raw.get("Currency", "USD"),
            "effective_date": _parse_dt(raw.get("EffectiveDate")),
            "raw_attributes": raw, "source_api": "aws_s3",
        })
    return records


def normalize_aws_rds(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("PricePerUnit", 0))
        if ppu is None:
            continue
        unit = raw.get("Unit", "Hrs")
        records.append({
            "vendor": "aws", "service_name": raw.get("serviceName", "Amazon RDS"),
            "category": "Database", "sku_id": raw.get("SKU", ""),
            "description": raw.get("PriceDescription", ""),
            "region": raw.get("Region Code", ""),
            "instance_type": raw.get("Instance Type") or None,
            "operating_system": raw.get("Database Engine") or None,
            "price_per_unit": ppu, "unit": unit,
            "price_per_hour": ppu if _is_hourly(unit) else None,
            "currency": raw.get("Currency", "USD"),
            "effective_date": _parse_dt(raw.get("EffectiveDate")),
            "raw_attributes": raw, "source_api": "aws_rds",
        })
    return records


def normalize_aws_cloudfront(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("PricePerUnit", 0))
        if ppu is None:
            continue
        unit = raw.get("Unit", "GB")
        records.append({
            "vendor": "aws", "service_name": raw.get("serviceName", "Amazon CloudFront"),
            "category": "CDN", "sku_id": raw.get("SKU", ""),
            "description": raw.get("PriceDescription", ""),
            "region": raw.get("Region Code") or raw.get("From Region Code", ""),
            "instance_type": None, "operating_system": None,
            "price_per_unit": ppu, "unit": unit,
            "price_per_hour": ppu if _is_hourly(unit) else None,
            "currency": raw.get("Currency", "USD"),
            "effective_date": _parse_dt(raw.get("EffectiveDate")),
            "raw_attributes": raw, "source_api": "aws_cloudfront",
        })
    return records


def normalize_azure(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("retailPrice", raw.get("unitPrice", 0)))
        if ppu is None:
            continue
        unit = raw.get("unitOfMeasure", "1 Hour")
        service = raw.get("serviceName", "Unknown")
        prod = raw.get("productName", "")
        sku_name = raw.get("skuName", "")
        desc = f"{prod} – {sku_name}".strip(" –")
        records.append({
            "vendor": "azure", "service_name": service,
            "category": _category_from_service(service),
            "sku_id": raw.get("skuId") or raw.get("meterId", ""),
            "description": desc,
            "region": raw.get("armRegionName", ""),
            "instance_type": raw.get("armSkuName") or sku_name or None,
            "operating_system": None, "price_per_unit": ppu, "unit": unit,
            "price_per_hour": ppu if _is_hourly(unit) else None,
            "currency": raw.get("currencyCode", "USD"),
            "effective_date": _parse_dt(raw.get("effectiveStartDate")),
            "raw_attributes": raw, "source_api": "azure",
        })
    return records


def normalize_gcp(payload: Dict) -> List[dict]:
    records = []
    for raw in payload.get("raw_records", []):
        ppu = _to_decimal(raw.get("priceUSD", 0))
        if ppu is None:
            continue
        unit = raw.get("usageUnit", "h")
        service = raw.get("service", "Compute Engine")
        regions = raw.get("serviceRegions", [])
        region = regions[0] if regions else ""
        records.append({
            "vendor": "gcp", "service_name": service,
            "category": _category_from_service(service),
            "sku_id": raw.get("skuId", ""),
            "description": raw.get("description", ""),
            "region": region,
            "instance_type": None, "operating_system": None,
            "price_per_unit": ppu, "unit": unit,
            "price_per_hour": ppu if _is_hourly(unit) else None,
            "currency": raw.get("currencyCode", "USD"),
            "effective_date": _parse_dt(raw.get("effectiveTime")),
            "raw_attributes": raw, "source_api": "gcp",
        })
    return records


SOURCE_NORMALIZERS = {
    "infracost": normalize_infracost,
    "aws_ec2": normalize_aws_ec2,
    "aws_s3": normalize_aws_s3,
    "aws_rds": normalize_aws_rds,
    "aws_cloudfront": normalize_aws_cloudfront,
    "azure": normalize_azure,
    "gcp": normalize_gcp,
}


def normalize_all(payloads: Dict[str, Dict]) -> List[dict]:
    """Given { source_name: raw_payload }, return a flat list of normalised pricing records."""
    all_records: List[dict] = []
    for source, payload in payloads.items():
        fn = SOURCE_NORMALIZERS.get(source)
        if fn is None:
            continue
        if payload.get("status") in ("skipped", "error"):
            continue
        all_records.extend(fn(payload))
    return all_records
