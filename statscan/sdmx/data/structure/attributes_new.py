from typing import Optional, Any, Union
from datetime import datetime, date

from pydantic import field_validator

from ...base import Base
from .relationship import Relationship


class AttributeValue(Base):
    """
    Represents a value for an attribute in SDMX.
    """

    id: Optional[Union[int, str]] = None
    order: Optional[int] = None
    name: Optional[str] = None
    names: Optional[dict[str, str]] = None  # language -> name mapping
    annotations: Optional[list[int]] = None
    value: Optional[Any] = None

    @field_validator("value", mode="before")
    @classmethod
    def parse_value(cls, value):
        """Parse string values to appropriate types."""
        if isinstance(value, str):
            # Convert empty strings to None
            if value == "":
                return None
            # Convert numeric strings to appropriate types
            try:
                if "." in value or "e" in value.lower():
                    return float(value)
                else:
                    return int(value)
            except ValueError:
                try:
                    return date.fromisoformat(value)
                except ValueError:
                    pass
                try:
                    return datetime.fromisoformat(value)
                except ValueError:
                    pass
        return value

    def get_display_name(self, language: str = "en") -> str:
        """Get the display name in the specified language."""
        if self.names:
            return self.names.get(language, self.name or str(self.id))
        return self.name or str(self.id)


class Attribute(Base):
    """
    Represents an attribute in SDMX structures.
    """

    id: str
    name: str
    names: Optional[dict[str, str]] = None  # language -> name mapping
    roles: Optional[list[str]] = None
    relationship: Optional[Relationship] = None
    values: list[AttributeValue] = []
    annotations: Optional[list[int]] = None

    def __getitem__(self, key: Union[int, str]) -> AttributeValue:
        """Get an attribute value by its ID."""
        for value in self.values:
            if value.id == key:
                return value
        raise KeyError(f"AttributeValue with ID '{key}' not found.")

    def get_display_name(self, language: str = "en") -> str:
        """Get the display name in the specified language."""
        if self.names:
            return self.names.get(language, self.name)
        return self.name

    def get_value_by_name(
        self, name: str, language: str = "en"
    ) -> Optional[AttributeValue]:
        """Get a value by its name or display name."""
        for value in self.values:
            if value.name == name or value.get_display_name(language) == name:
                return value
        return None


class Attributes(Base):
    """
    Represents the collection of attributes in SDMX structures.
    Based on actual structure: {dataSet (list), dimensionGroup (list), series (list), observation (list)}
    """

    dataSet: Optional[list] = None
    dimensionGroup: Optional[list] = None
    series: list[Attribute] = []
    observation: list[Attribute] = []

    def __getitem__(self, key: str) -> Attribute:
        """Get an attribute by its ID."""
        for attribute in self.series:
            if attribute.id == key:
                return attribute
        for attribute in self.observation:
            if attribute.id == key:
                return attribute
        raise KeyError(f"Attribute with ID '{key}' not found.")

    def get_attribute_by_name(
        self, name: str, language: str = "en"
    ) -> Optional[Attribute]:
        """Get an attribute by its name or display name."""
        for attribute in self.series + self.observation:
            if attribute.name == name or attribute.get_display_name(language) == name:
                return attribute
        return None

    def get_series_attribute(self, attribute_id: str) -> Optional[Attribute]:
        """Get a series-level attribute by ID."""
        for attribute in self.series:
            if attribute.id == attribute_id:
                return attribute
        return None

    def get_observation_attribute(self, attribute_id: str) -> Optional[Attribute]:
        """Get an observation-level attribute by ID."""
        for attribute in self.observation:
            if attribute.id == attribute_id:
                return attribute
        return None

    @property
    def series_attribute_ids(self) -> list[str]:
        """Get all series attribute IDs."""
        return [attr.id for attr in self.series]

    @property
    def series_attribute_names(self) -> list[str]:
        """Get all series attribute names."""
        return [attr.name for attr in self.series]

    @property
    def observation_attribute_ids(self) -> list[str]:
        """Get all observation attribute IDs."""
        return [attr.id for attr in self.observation]

    @property
    def observation_attribute_names(self) -> list[str]:
        """Get all observation attribute names."""
        return [attr.name for attr in self.observation]

    @property
    def all_attributes(self) -> list[Attribute]:
        """Get all attributes (series + observation)."""
        return self.series + self.observation
