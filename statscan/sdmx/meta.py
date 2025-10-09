"""SDMX metadata and sender information models."""

from datetime import datetime

from pydantic import Field

from .base import Base


class Sender(Base):
    """Sender information for SDMX responses."""

    id: str
    name: str
    names: dict[str, str] | None = None  # language -> name mapping (optional)
    contacts: list | None = None  # Optional contacts field

    def get_display_name(self, lang: str = "en") -> str:
        """Get the display name in the specified language, defaulting to 'en'."""
        if self.names:
            return self.names.get(lang, self.name)
        return self.name


class Metadata(Base):
    """Metadata for SDMX responses including sender and language information."""

    response_schema: str = Field(alias="schema")
    id: str
    prepared: datetime
    test: bool | None = None
    contentLanguages: list[str] | None = None  # noqa: N815
    sender: Sender

    @classmethod
    def _preprocess_data(cls, data: dict) -> dict:
        # Allow tests providing 'schema' or 'response_schema'
        if "response_schema" in data and "schema" not in data:
            data["schema"] = data["response_schema"]
        return data
