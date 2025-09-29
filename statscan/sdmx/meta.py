from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import Base


class Sender(Base):
    id: str
    name: str
    names: Optional[dict[str, str]] = None  # language -> name mapping (optional)
    contacts: Optional[list] = None  # Optional contacts field

    def get_display_name(self, lang: str = "en") -> str:
        """Get the display name in the specified language, defaulting to 'en'."""
        if self.names:
            return self.names.get(lang, self.name)
        return self.name


class Metadata(Base):
    response_schema: str = Field(alias="schema")
    id: str
    prepared: datetime
    test: Optional[bool] = None
    contentLanguages: Optional[list[str]] = None
    sender: Sender

    @classmethod
    def _preprocess_data(cls, data: dict) -> dict:
        # Allow tests providing 'schema' or 'response_schema'
        if "response_schema" in data and "schema" not in data:
            data["schema"] = data["response_schema"]
        return data
