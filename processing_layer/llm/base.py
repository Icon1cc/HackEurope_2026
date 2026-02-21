from abc import ABC, abstractmethod
from pydantic import BaseModel


class LLMProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str: ...

    @abstractmethod
    def generate_from_image(self, prompt: str, image_bytes: bytes, mime_type: str) -> str: ...

    @abstractmethod
    def generate_structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel: ...

    @abstractmethod
    def generate_structured_from_image(
        self, prompt: str, image_bytes: bytes, mime_type: str, schema: type[BaseModel]
    ) -> BaseModel: ...
