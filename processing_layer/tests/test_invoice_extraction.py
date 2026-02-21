"""Integration tests for invoice extraction against FiftyOne ground truth."""
import pytest


def test_invoice_header_fields(annotated_sample, extractor):
    result = extractor.extract_from_image(
        annotated_sample["image_bytes"], annotated_sample["mime_type"]
    )
    gt_inv = annotated_sample["ground_truth"]["invoice"]

    assert result.invoice_number == gt_inv["invoice_number"]
    assert result.invoice_date   == gt_inv["invoice_date"]
    assert result.vendor_name    == gt_inv["seller_name"]
    assert result.client_name    == gt_inv["client_name"]
    assert result.vendor_address == gt_inv["seller_address"]
    assert result.client_address == gt_inv["client_address"]


def test_invoice_total(annotated_sample, extractor):
    result = extractor.extract_from_image(
        annotated_sample["image_bytes"], annotated_sample["mime_type"]
    )
    gt_total = float(annotated_sample["ground_truth"]["subtotal"]["total"])

    assert result.total is not None
    assert abs(result.total - gt_total) < 0.01


def test_invoice_line_item_count(annotated_sample, extractor):
    result = extractor.extract_from_image(
        annotated_sample["image_bytes"], annotated_sample["mime_type"]
    )
    gt_items = annotated_sample["ground_truth"]["items"]

    assert len(result.line_items) == len(gt_items)


def test_invoice_line_item_totals(annotated_sample, extractor):
    """Line item gross totals should match ground truth (GT stores gross prices)."""
    result = extractor.extract_from_image(
        annotated_sample["image_bytes"], annotated_sample["mime_type"]
    )
    gt_items = annotated_sample["ground_truth"]["items"]

    for i, (ext_item, gt_item) in enumerate(zip(result.line_items, gt_items)):
        gt_total = float(gt_item["total_price"])
        assert abs(ext_item.total_price - gt_total) < 0.01, (
            f"Line item {i+1}: extracted {ext_item.total_price} != GT {gt_total}"
        )
