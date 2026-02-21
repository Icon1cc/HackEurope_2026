import json
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

# make `processing_layer` importable from repo root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv(Path(__file__).parent.parent.parent / ".env")


@pytest.fixture(scope="session")
def annotated_sample():
    """Load one annotated invoice sample from the FiftyOne HuggingFace dataset."""
    from fiftyone.utils.huggingface import load_from_hub

    dataset = load_from_hub(
        "Voxel51/high-quality-invoice-images-for-ocr",
        max_samples=10,
    )
    sample = next(s for s in dataset if s["json_annotation"] is not None)
    return {
        "image_bytes": Path(sample.filepath).read_bytes(),
        "mime_type": "image/jpeg",
        "ground_truth": json.loads(sample["json_annotation"]),
    }


@pytest.fixture(scope="session")
def extractor():
    from processing_layer.extraction.invoice import InvoiceExtractor
    from processing_layer.llm.gemini import GeminiProvider

    return InvoiceExtractor(GeminiProvider())
