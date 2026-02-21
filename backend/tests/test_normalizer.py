"""Unit tests for the pricing normalizer — pure logic, no DB needed."""

import pytest
from decimal import Decimal

from app.pricing.normalizer import (
    normalize_all,
    normalize_aws_ec2,
    normalize_aws_s3,
    normalize_azure,
    normalize_gcp,
    normalize_infracost,
    _is_hourly,
    _to_decimal,
    _category_from_service,
)


class TestHelpers:
    def test_is_hourly(self):
        assert _is_hourly("Hrs") is True
        assert _is_hourly("hour") is True
        assert _is_hourly("h") is True
        assert _is_hourly("1 Hour") is True
        assert _is_hourly("GB") is False
        assert _is_hourly("Requests") is False

    def test_to_decimal(self):
        assert _to_decimal("0.046") == Decimal("0.046")
        assert _to_decimal(0.5) == Decimal("0.5")
        assert _to_decimal("invalid") is None
        assert _to_decimal(None) is None

    def test_category_from_service(self):
        assert _category_from_service("Amazon EC2") == "Compute"
        assert _category_from_service("Compute Engine") == "Compute"
        assert _category_from_service("Amazon S3") == "Storage"
        assert _category_from_service("Blob Storage") == "Storage"
        assert _category_from_service("Amazon RDS") == "Database"
        assert _category_from_service("Cloud SQL") == "Database"
        assert _category_from_service("Amazon CloudFront") == "CDN"
        assert _category_from_service("SomeOther") == "Other"


class TestNormalizeAwsEc2:
    def test_basic(self):
        payload = {
            "raw_records": [{
                "SKU": "ABC123",
                "serviceName": "Amazon Elastic Compute Cloud",
                "PricePerUnit": "0.046",
                "Unit": "Hrs",
                "PriceDescription": "On Demand Linux",
                "Instance Type": "t3.micro",
                "Operating System": "Linux",
                "Region Code": "eu-west-1",
                "Currency": "USD",
                "EffectiveDate": "2024-01-01",
            }]
        }
        records = normalize_aws_ec2(payload)
        assert len(records) == 1
        r = records[0]
        assert r["vendor"] == "aws"
        assert r["sku_id"] == "ABC123"
        assert r["price_per_unit"] == Decimal("0.046")
        assert r["price_per_hour"] == Decimal("0.046")
        assert r["instance_type"] == "t3.micro"
        assert r["source_api"] == "aws_ec2"

    def test_non_hourly_sku(self):
        payload = {
            "raw_records": [{
                "SKU": "XYZ",
                "PricePerUnit": "0.023",
                "Unit": "GB",
                "serviceName": "Amazon S3",
            }]
        }
        records = normalize_aws_ec2(payload)
        assert len(records) == 1
        assert records[0]["price_per_hour"] is None

    def test_empty(self):
        assert normalize_aws_ec2({"raw_records": []}) == []
        assert normalize_aws_ec2({}) == []


class TestNormalizeAwsS3:
    def test_basic(self):
        payload = {
            "raw_records": [{
                "SKU": "S3SKU",
                "serviceName": "Amazon Simple Storage Service",
                "PricePerUnit": "0.023",
                "Unit": "GB",
                "Region Code": "eu-west-1",
                "Currency": "USD",
            }]
        }
        records = normalize_aws_s3(payload)
        assert len(records) == 1
        assert records[0]["category"] == "Storage"
        assert records[0]["price_per_hour"] is None


class TestNormalizeAzure:
    def test_basic(self):
        payload = {
            "raw_records": [{
                "retailPrice": 0.096,
                "unitOfMeasure": "1 Hour",
                "serviceName": "Virtual Machines",
                "productName": "Standard_D2s_v3",
                "skuName": "D2s v3",
                "skuId": "az-sku-123",
                "armRegionName": "westeurope",
                "armSkuName": "Standard_D2s_v3",
                "currencyCode": "USD",
            }]
        }
        records = normalize_azure(payload)
        assert len(records) == 1
        r = records[0]
        assert r["vendor"] == "azure"
        assert r["price_per_hour"] == Decimal("0.096")
        assert r["category"] == "Compute"


class TestNormalizeGcp:
    def test_basic(self):
        payload = {
            "raw_records": [{
                "skuId": "gcp-sku-1",
                "description": "N1 Standard 2",
                "service": "Compute Engine",
                "serviceRegions": ["europe-west1"],
                "usageUnit": "h",
                "priceUSD": 0.0950,
                "currencyCode": "USD",
            }]
        }
        records = normalize_gcp(payload)
        assert len(records) == 1
        r = records[0]
        assert r["vendor"] == "gcp"
        assert r["price_per_hour"] == Decimal("0.095")
        assert r["category"] == "Compute"


class TestNormalizeAll:
    def test_skips_errors(self):
        payloads = {
            "aws_ec2": {"status": "error", "error": "timeout"},
            "aws_s3": {
                "raw_records": [{
                    "SKU": "S3OK",
                    "PricePerUnit": "0.023",
                    "Unit": "GB",
                    "serviceName": "Amazon S3",
                }]
            },
        }
        records = normalize_all(payloads)
        assert len(records) == 1
        assert records[0]["sku_id"] == "S3OK"

    def test_skips_unknown_source(self):
        payloads = {"unknown_source": {"raw_records": [{"foo": "bar"}]}}
        records = normalize_all(payloads)
        assert records == []

    def test_skips_skipped_sources(self):
        payloads = {"gcp": {"status": "skipped", "reason": "no key"}}
        records = normalize_all(payloads)
        assert records == []
