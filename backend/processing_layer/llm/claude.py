import os

from anthropic import Anthropic
from pydantic import BaseModel

from .base import LLMProvider

DEFAULT_MODEL = "claude-sonnet-4-6"


class ClaudeProvider(LLMProvider):
    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None):
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        assert key, "ANTHROPIC_API_KEY env var not set"
        self.client = Anthropic(api_key=key)
        self.model = model

    def generate_text(self, prompt: str) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def generate_from_image(self, prompt: str, image_bytes: bytes, mime_type: str) -> str:
        raise NotImplementedError("Use GeminiProvider for image extraction")

    def generate_structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            tools=[{
                "name": "output",
                "description": f"Return a structured {schema.__name__}",
                "input_schema": schema.model_json_schema(),
            }],
            tool_choice={"type": "tool", "name": "output"},
            messages=[{"role": "user", "content": prompt}],
        )
        for block in message.content:
            if block.type == "tool_use" and block.name == "output":
                return schema.model_validate(block.input)
        raise RuntimeError(f"Claude did not return tool_use block for {schema.__name__}")

    def generate_structured_from_image(
        self, prompt: str, image_bytes: bytes, mime_type: str, schema: type[BaseModel]
    ) -> BaseModel:
        raise NotImplementedError("Use GeminiProvider for image extraction")
