from typing import Optional, Union

from ..relationship import Relationship
from ..value import Value
from ....base import Base


class Observation(Base):
    """
    Represents an observation dimension in SDMX.
    Based on actual structure: {id (str), name (str), names (dict), keyPosition (int), roles (list), values (list)}
    """

    id: str
    name: str
    names: Optional[dict[str, str]] = None  # language -> name mapping
    keyPosition: Optional[int] = None
    roles: Optional[list[str]] = None
    relationship: Optional[Relationship] = None
    values: list[Value] = []

    def __getitem__(self, key: Union[int, str]) -> Value:
        """Get an observation value by its ID."""
        for value in self.values:
            if value.id == key:
                return value
        raise KeyError(f"ObservationValue with ID '{key}' not found.")

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

    @property
    def has_time_values(self) -> bool:
        """Check if this observation dimension contains time-based values."""
        return any(value.is_time_period for value in self.values)

    @property
    def time_range(self) -> Optional[tuple]:
        """Get the overall time range if this is a time dimension."""
        if not self.has_time_values:
            return None

        start_dates = [v.start for v in self.values if v.start]
        end_dates = [v.end for v in self.values if v.end]

        if start_dates and end_dates:
            return (min(start_dates), max(end_dates))
        return None
