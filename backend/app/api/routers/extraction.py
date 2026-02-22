from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, UploadFile, File

from processing_layer.extraction import InvoiceExtractor
from processing_layer.llm import get_provider

load_dotenv()

router = APIRouter(prefix="/extraction", tags=["extraction"])

_executor = ThreadPoolExecutor(max_workers=4)

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}


@router.post("/")
async def extract_invoice(file: UploadFile = File(...)):
    """
    Upload an invoice (PDF or image), extract structured data via Gemini,
    and return the extraction result. No DB persistence — results stay in RAM.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    loop = asyncio.get_event_loop()
    provider = get_provider("gemini")
    extractor = InvoiceExtractor(provider)

    is_pdf = file.content_type == "application/pdf"

    if is_pdf:
        extraction = await loop.run_in_executor(
            _executor,
            extractor.extract_from_pdf,
            file_bytes,
        )
    else:
        extraction = await loop.run_in_executor(
            _executor,
            extractor.extract_from_image,
            file_bytes,
            file.content_type,
        )

    return extraction.model_dump()
