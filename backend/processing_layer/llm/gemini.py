import os
import tempfile

from google import genai
from google.genai import types
from pydantic import BaseModel

from .base import LLMProvider
from ..constants import DEFAULT_MODEL

SUPPORTED_IMAGE_MIME_TYPES = frozenset({
    "image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"
})


class GeminiProvider(LLMProvider):
    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None):
        key = api_key or os.environ["GEMINI_API_KEY"]
        self.client = genai.Client(api_key=key)
        self.model = model

    def generate_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        assert response.text is not None, "Gemini returned no text"
        return response.text

    def generate_from_image(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        assert mime_type in SUPPORTED_IMAGE_MIME_TYPES, f"Unsupported image MIME type: {mime_type}"
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        response = self.client.models.generate_content(
            model=self.model, contents=[part, prompt]
        )
        assert response.text is not None, "Gemini returned no text"
        return response.text

    def generate_structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema.model_json_schema(),
        )
        response = self.client.models.generate_content(
            model=self.model, contents=prompt, config=config
        )
        assert response.text is not None, "Gemini returned no text"
        return schema.model_validate_json(response.text)

    def generate_structured_from_image(
        self, prompt: str, image_bytes: bytes, mime_type: str, schema: type[BaseModel]
    ) -> BaseModel:
        assert mime_type in SUPPORTED_IMAGE_MIME_TYPES, f"Unsupported image MIME type: {mime_type}"
        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema.model_json_schema(),
        )
        response = self.client.models.generate_content(
            model=self.model, contents=[part, prompt], config=config
        )
        assert response.text is not None, "Gemini returned no text"
        return schema.model_validate_json(response.text)

    def generate_structured_from_pdf(self, prompt: str, pdf_bytes: bytes, schema: type[BaseModel]) -> BaseModel:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            tmp_path = f.name

        uploaded = self.client.files.upload(file=tmp_path, config={"mime_type": "application/pdf"})
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=schema.model_json_schema(),
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=[types.Part.from_uri(file_uri=uploaded.uri, mime_type="application/pdf"), prompt],
            config=config,
        )
        self.client.files.delete(name=uploaded.name)
        os.unlink(tmp_path)

        assert response.text is not None, "Gemini returned no text"
        return schema.model_validate_json(response.text)
