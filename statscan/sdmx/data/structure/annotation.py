"""SDMX annotation models for metadata and text descriptions."""

from pydantic import field_validator

from ...base import Base


class Annotation(Base):
    """Represents an annotation in SDMX structures.

    Based on the actual SDMX structure: {type (str), text (str), texts (dict)}.

    """

    id: str | None = None  # Make optional to handle incomplete annotations
    text: str | int | bool | None = None
    title: str | None = None
    type: str | None = None  # Make optional to handle incomplete annotations
    texts: dict[str, str] | None = None  # language -> text mapping

    def get_display_text(self, language: str = "en") -> str:
        """Get the display text in the specified language, fallback to text."""
        if self.texts:
            return self.texts.get(
                language, str(self.text) if self.text is not None else ""
            )
        return str(self.text) if self.text is not None else ""

    @field_validator("text", mode="before")
    def validate_text(self, value: str | int | bool) -> str | int | bool:
        """Validate and convert text values to appropriate types."""
        if isinstance(value, str):
            if value.isdigit():
                return int(value)
            elif value.lower() in ("true", "false"):
                return value.lower() == "true"
        return value

    @property
    def is_boolean_flag(self) -> bool:
        """Check if this annotation represents a boolean flag."""
        return isinstance(self.text, bool) or (
            isinstance(self.text, str) and self.text.lower() in ("true", "false")
        )

    @property
    def boolean_value(self) -> bool | None:
        """Get the boolean value if this is a boolean flag."""
        if isinstance(self.text, bool):
            return self.text
        elif isinstance(self.text, str) and self.text.lower() in ("true", "false"):
            return self.text.lower() == "true"
        return None
