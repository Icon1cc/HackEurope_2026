from ..llm.base import LLMProvider
from ..prompts import INVOICE_EXTRACTION_PROMPT
from ..schemas.invoice import InvoiceExtraction


class InvoiceExtractor:
    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def extract_from_image(self, image_bytes: bytes, mime_type: str) -> InvoiceExtraction:
        result = self.provider.generate_structured_from_image(
            prompt=INVOICE_EXTRACTION_PROMPT,
            image_bytes=image_bytes,
            mime_type=mime_type,
            schema=InvoiceExtraction,
        )
        assert isinstance(result, InvoiceExtraction), f"Unexpected result type: {type(result)}"
        return result

    def extract_from_pdf(self, pdf_bytes: bytes) -> InvoiceExtraction:
        from ..llm.gemini import GeminiProvider
        assert isinstance(self.provider, GeminiProvider), \
            "PDF extraction via File API only supported for GeminiProvider"
        result = self.provider.generate_structured_from_pdf(
            prompt=INVOICE_EXTRACTION_PROMPT,
            pdf_bytes=pdf_bytes,
            schema=InvoiceExtraction,
        )
        assert isinstance(result, InvoiceExtraction), f"Unexpected result type: {type(result)}"
        return result
