from typing import Union, Optional

from ....base import Base
from ..value import Value


class Series(Base):
    """
    Represents a series dimension in SDMX.
    Based on actual structure: {id (str), name (str), names (dict), keyPosition (int), roles (list), values (list)}
    """

    id: str
    name: str
    names: Optional[dict[str, str]] = None  # language -> name mapping
    keyPosition: Optional[int] = None
    roles: Optional[list[str]] = None
    values: list[Value] = []
    annotations: Optional[list[int]] = None

    def __getitem__(self, key: Union[int, str]) -> Value:
        """Get a value by its ID."""
        for value in self.values:
            if value.id == key:
                return value
        raise KeyError(f"Value with ID '{key}' not found.")

    def get_display_name(self, language: str = "en") -> str:
        """Get the display name in the specified language."""
        if self.names:
            return self.names.get(language, self.name)
        return self.name

    def get_value_by_name(self, name: str, language: str = "en") -> Optional[Value]:
        """Get a value by its name or display name."""
        for value in self.values:
            if value.name == name or value.get_display_name(language) == name:
                return value
        return None

    # def get_values_by_order(self) -> list[Value]:
    #     """Get values sorted by their order property."""
    #     values_
    #     s = sorted([v for v in self.values if v.order is not None], key=lambda x: x.order)  # type: ignore[arg-type]

    @property
    def has_ordered_values(self) -> bool:
        """Check if values have ordering information."""
        return any(value.order is not None for value in self.values)
