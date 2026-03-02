"""
InvoiceGuard — JSON → cloud_pricing DB Transformer
====================================================
Reads all raw_*.json files and transforms each record into the
cloud_pricing schema, ready for DB insertion or upsert via FastAPI.

Outputs:
  transformed_cloud_pricing.json  — all records in DB shape
  transform_report.json           — per-source stats + any warnings

Usage:
  python transform_to_db.py

  Or import and call transform_all() from another script.
"""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────
INPUT_DIR  = Path(__file__).parent  # same directory as the raw JSON files
OUTPUT_DIR = Path(__file__).parent / "transformed"
OUTPUT_DIR.mkdir(exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────

def load(filename: str) -> dict:
    """Load a raw JSON file from INPUT_DIR, or from cwd as fallback."""
    paths = [
        INPUT_DIR / filename,
        Path(filename),
    ]
    for p in paths:
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError(f"Cannot find {filename}")


def to_decimal(value) -> float | None:
    """Safely convert any value to a plain Python float for JSON output."""
    if value is None or value == "":
        return None
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_date(value: str) -> str | None:
    """Return ISO-8601 string or None. Accepts date-only strings like '2026-02-01'."""
    if not value:
        return None
    try:
        # Try full ISO first
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.isoformat()
    except ValueError:
        pass
    try:
        # Date-only "YYYY-MM-DD"
        dt = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def categorise_aws(product_family: str, service_code: str) -> str:
    """Map AWS Product Family → our category enum."""
    pf = (product_family or "").lower()
    sc = (service_code or "").lower()
    if "compute" in pf or "ec2" in sc:
        return "Compute"
    if "storage" in pf or "s3" in sc:
        return "Storage"
    if "database" in pf or "rds" in sc:
        return "Database"
    if "transfer" in pf or "data transfer" in pf:
        return "Data Transfer"
    if "cloudfront" in sc or "cdn" in pf:
        return "CDN"
    if "request" in pf or "api" in pf:
        return "API / Requests"
    if "serverless" in pf:
        return "Serverless"
    return "Other"


def categorise_gcp(resource_family: str, resource_group: str) -> str:
    rf = (resource_family or "").lower()
    rg = (resource_group or "").lower()
    if "compute" in rf:
        return "Compute"
    if "storage" in rf:
        return "Storage"
    if "database" in rf or "sql" in rg:
        return "Database"
    if "network" in rf:
        return "Networking"
    return "Other"


def categorise_azure(service_family: str, service_name: str) -> str:
    sf = (service_family or "").lower()
    sn = (service_name or "").lower()
    if "compute" in sf or "virtual machine" in sn:
        return "Compute"
    if "storage" in sf or "storage" in sn:
        return "Storage"
    if "database" in sf or "sql" in sn:
        return "Database"
    if "network" in sf:
        return "Networking"
    if "kubernetes" in sn or "container" in sn:
        return "Containers"
    return "Other"


# ═══════════════════════════════════════════════════════════════════════════
# SOURCE TRANSFORMERS
# Each returns a list of dicts matching cloud_pricing columns.
# ═══════════════════════════════════════════════════════════════════════════

def transform_infracost(raw: dict) -> list[dict]:
    results = []
    for rec in raw.get("raw_records", []):
        attrs = {a["key"]: a["value"] for a in rec.get("attributes", [])}
        vendor = (rec.get("vendorName") or "").lower()
        sku_id = (
            attrs.get("meterId")
            or attrs.get("skuId")
            or attrs.get("productId")
            or attrs.get("skuName")
            or "UNKNOWN"
        )
        prices = rec.get("prices") or []

        if not prices:
            unit = attrs.get("unitOfMeasure") or None
            results.append({
                "vendor":           vendor,
                "service_name":     rec.get("service") or "",
                "category":         categorise_azure(
                    attrs.get("serviceFamily", ""),
                    rec.get("service", ""),
                ),
                "sku_id":           sku_id,
                "description":      attrs.get("productName") or attrs.get("skuName"),
                "region":           rec.get("region"),
                "instance_type":    attrs.get("armSkuName") or attrs.get("skuName"),
                "operating_system": None,
                "price_per_unit":   None,
                "unit":             unit,
                "price_per_hour":   None,
                "currency":         "USD",
                "effective_date":   parse_date(attrs.get("effectiveStartDate")),
                "raw_attributes":   rec,
                "source_api":       "infracost",
            })
        else:
            for price in prices:
                unit     = price.get("unit") or None
                usd_val  = to_decimal(price.get("USD"))
                pph = usd_val if unit and "hour" in unit.lower() else None
                results.append({
                    "vendor":           vendor,
                    "service_name":     rec.get("service") or "",
                    "category":         categorise_azure(
                        attrs.get("serviceFamily", ""),
                        rec.get("service", ""),
                    ),
                    "sku_id":           sku_id,
                    "description":      price.get("description") or attrs.get("productName"),
                    "region":           rec.get("region"),
                    "instance_type":    attrs.get("armSkuName") or attrs.get("skuName"),
                    "operating_system": None,
                    "price_per_unit":   usd_val,
                    "unit":             unit,
                    "price_per_hour":   pph,
                    "currency":         "USD",
                    "effective_date":   parse_date(price.get("effectiveDateStart")),
                    "raw_attributes":   rec,
                    "source_api":       "infracost",
                })
    return results


def transform_aws_ec2(raw: dict) -> list[dict]:
    results = []
    for rec in raw.get("raw_records", []):
        unit      = rec.get("Unit") or None
        ppu       = to_decimal(rec.get("PricePerUnit"))
        is_hourly = unit and unit.lower() in ("hrs", "hours", "hr", "h")
        pph       = ppu if is_hourly else None
        os_raw = rec.get("Operating System") or ""
        os_map = {"Linux": "Linux", "Windows": "Windows", "RHEL": "RHEL", "SUSE": "SUSE"}
        operating_system = os_map.get(os_raw, os_raw or None)
        results.append({
            "vendor":           "aws",
            "service_name":     rec.get("serviceName") or "Amazon EC2",
            "category":         categorise_aws(
                rec.get("Product Family", ""),
                rec.get("serviceCode", "AmazonEC2"),
            ),
            "sku_id":           rec.get("SKU") or rec.get("RateCode") or "",
            "description":      rec.get("PriceDescription"),
            "region":           rec.get("Region Code") or None,
            "instance_type":    rec.get("Instance Type") or None,
            "operating_system": operating_system,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   pph,
            "currency":         rec.get("Currency") or "USD",
            "effective_date":   parse_date(rec.get("EffectiveDate")),
            "raw_attributes":   rec,
            "source_api":       "aws_ec2",
        })
    return results


def transform_aws_s3(raw: dict) -> list[dict]:
    results = []
    for rec in raw.get("raw_records", []):
        unit  = rec.get("Unit") or None
        ppu   = to_decimal(rec.get("PricePerUnit"))
        region = rec.get("Region Code") or rec.get("From Region Code") or None
        results.append({
            "vendor":           "aws",
            "service_name":     rec.get("serviceName") or "Amazon S3",
            "category":         "Storage",
            "sku_id":           rec.get("SKU") or rec.get("RateCode") or "",
            "description":      rec.get("PriceDescription"),
            "region":           region,
            "instance_type":    None,
            "operating_system": None,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   None,
            "currency":         rec.get("Currency") or "USD",
            "effective_date":   parse_date(rec.get("EffectiveDate")),
            "raw_attributes":   rec,
            "source_api":       "aws_s3",
        })
    return results


def transform_aws_rds(raw: dict) -> list[dict]:
    results = []
    for rec in raw.get("raw_records", []):
        unit  = rec.get("Unit") or None
        ppu   = to_decimal(rec.get("PricePerUnit"))
        pph   = ppu if unit and unit.lower() in ("hrs", "h") else None
        db_engine = rec.get("Database Engine") or None
        results.append({
            "vendor":           "aws",
            "service_name":     rec.get("serviceName") or "Amazon RDS",
            "category":         "Database",
            "sku_id":           rec.get("SKU") or rec.get("RateCode") or "",
            "description":      rec.get("PriceDescription"),
            "region":           rec.get("Region Code") or None,
            "instance_type":    rec.get("Instance Type") or None,
            "operating_system": db_engine,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   pph,
            "currency":         rec.get("Currency") or "USD",
            "effective_date":   parse_date(rec.get("EffectiveDate")),
            "raw_attributes":   rec,
            "source_api":       "aws_rds",
        })
    return results


def transform_aws_cloudfront(raw: dict) -> list[dict]:
    results = []
    for rec in raw.get("raw_records", []):
        unit   = rec.get("Unit") or None
        ppu    = to_decimal(rec.get("PricePerUnit"))
        region = rec.get("Region Code") or rec.get("From Region Code") or None
        location = rec.get("Location") or rec.get("From Location") or None
        if not region and location:
            region = location
        results.append({
            "vendor":           "aws",
            "service_name":     rec.get("serviceName") or "Amazon CloudFront",
            "category":         "CDN",
            "sku_id":           rec.get("SKU") or rec.get("RateCode") or "",
            "description":      rec.get("PriceDescription"),
            "region":           region,
            "instance_type":    None,
            "operating_system": None,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   None,
            "currency":         rec.get("Currency") or "USD",
            "effective_date":   parse_date(rec.get("EffectiveDate")),
            "raw_attributes":   rec,
            "source_api":       "aws_cloudfront",
        })
    return results


def transform_azure(raw: dict) -> list[dict]:
    results = []
    for rec in raw.get("raw_records", []):
        unit    = rec.get("unitOfMeasure") or None
        ppu     = to_decimal(rec.get("retailPrice") or rec.get("unitPrice"))
        is_hourly = unit and ("hour" in unit.lower() or "hr" in unit.lower())
        pph = ppu if is_hourly else None
        product_name = rec.get("productName") or ""
        if "windows" in product_name.lower():
            os_val = "Windows"
        elif "linux" in product_name.lower():
            os_val = "Linux"
        else:
            os_val = None
        results.append({
            "vendor":           "azure",
            "service_name":     rec.get("serviceName") or "",
            "category":         categorise_azure(
                rec.get("serviceFamily", ""),
                rec.get("serviceName", ""),
            ),
            "sku_id":           rec.get("skuId") or rec.get("meterId") or "",
            "description":      f"{product_name} — {rec.get('meterName', '')}".strip(" — "),
            "region":           rec.get("armRegionName") or None,
            "instance_type":    rec.get("armSkuName") or rec.get("skuName") or None,
            "operating_system": os_val,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   pph,
            "currency":         rec.get("currencyCode") or "USD",
            "effective_date":   parse_date(rec.get("effectiveStartDate")),
            "raw_attributes":   rec,
            "source_api":       "azure",
        })
    return results


def transform_gcp(raw: dict) -> list[dict]:
    results = []
    for rec in raw.get("raw_records", []):
        ppu  = to_decimal(rec.get("priceUSD"))
        unit = rec.get("usageUnit") or rec.get("usageUnitDescription") or None
        regions = rec.get("serviceRegions") or []
        region  = regions[0] if len(regions) == 1 else (", ".join(regions) if regions else None)
        cat_info = rec.get("category") or {}
        category = categorise_gcp(
            cat_info.get("resourceFamily", ""),
            cat_info.get("resourceGroup", ""),
        )
        is_hourly = unit and unit.lower() in ("h", "hour", "hours", "hr")
        pph = ppu if is_hourly else None
        results.append({
            "vendor":           "gcp",
            "service_name":     rec.get("service") or "",
            "category":         category,
            "sku_id":           rec.get("skuId") or "",
            "description":      rec.get("description"),
            "region":           region,
            "instance_type":    None,
            "operating_system": None,
            "price_per_unit":   ppu,
            "unit":             unit,
            "price_per_hour":   pph,
            "currency":         rec.get("currencyCode") or "USD",
            "effective_date":   parse_date(rec.get("effectiveTime")),
            "raw_attributes":   rec,
            "source_api":       "gcp",
        })
    return results


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

SOURCES = [
    ("raw_1_infracost.json",      transform_infracost),
    ("raw_2_aws_ec2.json",        transform_aws_ec2),
    ("raw_3_aws_s3.json",         transform_aws_s3),
    ("raw_4_aws_rds.json",        transform_aws_rds),
    ("raw_5_aws_cloudfront.json", transform_aws_cloudfront),
    ("raw_6_azure.json",          transform_azure),
    ("raw_7_gcp.json",            transform_gcp),
]


def transform_all() -> tuple[list[dict], list[dict]]:
    all_records = []
    report      = []

    for filename, transformer in SOURCES:
        try:
            raw        = load(filename)
            records    = transformer(raw)
            ts         = now_iso()

            for r in records:
                r["created_at"] = ts
                r["updated_at"] = ts

            all_records.extend(records)
            report.append({
                "file":         filename,
                "source_api":   records[0]["source_api"] if records else "unknown",
                "status":       "ok",
                "records_in":   len(raw.get("raw_records", [])),
                "records_out":  len(records),
                "warnings":     [],
            })
            print(f"  ✅  {filename:<40} → {len(records):>4} DB records")

        except FileNotFoundError:
            print(f"  ⚠️   {filename:<40} → NOT FOUND (skipped)")
            report.append({
                "file":    filename,
                "status":  "skipped",
                "reason":  "file not found",
            })
        except Exception as exc:
            print(f"  ❌  {filename:<40} → ERROR: {exc}")
            report.append({
                "file":    filename,
                "status":  "error",
                "error":   str(exc),
            })

    return all_records, report


def validate(records: list[dict]) -> list[str]:
    warnings = []
    required = {"vendor", "service_name", "category", "sku_id", "source_api"}

    for i, r in enumerate(records):
        missing = required - {k for k, v in r.items() if v}
        if missing:
            warnings.append(f"Record {i}: missing required fields {missing}")
        if r.get("price_per_unit") is not None and r["price_per_unit"] < 0:
            warnings.append(f"Record {i}: negative price_per_unit ({r['price_per_unit']})")
        if r.get("price_per_hour") is not None and r.get("unit"):
            if r["unit"].lower() not in ("hrs", "h", "hour", "hours", "hr", "1 hour"):
                warnings.append(
                    f"Record {i}: price_per_hour set but unit='{r['unit']}' — verify"
                )

    return warnings


if __name__ == "__main__":
    print("\n🔄  InvoiceGuard — JSON → cloud_pricing transformer\n")

    records, report = transform_all()

    warnings = validate(records)
    if warnings:
        print(f"\n⚠️   {len(warnings)} validation warnings:")
        for w in warnings[:20]:
            print(f"   {w}")
        if len(warnings) > 20:
            print(f"   … and {len(warnings) - 20} more")

    out_path = OUTPUT_DIR / "transformed_cloud_pricing.json"
    with open(out_path, "w") as f:
        json.dump(records, f, indent=2, default=str)

    report_path = OUTPUT_DIR / "transform_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "run_at":         now_iso(),
            "total_records":  len(records),
            "total_warnings": len(warnings),
            "warnings":       warnings,
            "sources":        report,
        }, f, indent=2)

    print(f"\n📦  Total DB records : {len(records)}")
    print(f"⚠️   Validation warns : {len(warnings)}")
    print(f"📄  Output           : {out_path}")
    print(f"📊  Report           : {report_path}\n")

    if records:
        print("── Sample record (first) ──────────────────────────────────────")
        sample = {k: v for k, v in records[0].items() if k != "raw_attributes"}
        for k, v in sample.items():
            print(f"  {k:<20} : {v}")
        print()
