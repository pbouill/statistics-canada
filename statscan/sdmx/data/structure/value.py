
from typing import Optional, Union, List
from datetime import datetime

from pydantic import field_validator

from ...base import Base


class Value(Base):
    """
    Represents a value in an SDMX dimension or codelist.
    Based on actual structure: {start (str), end (str), id (str), name (str), names (dict)}
    """
    id: Union[int, str]  # Can be either int or string
    order: Optional[int] = None
    name: str
    names: Optional[dict[str, str]] = None  # language -> name mapping
    # For time dimensions
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    # Hierarchical relationships
    parent: Optional[str] = None
    parents: Optional[List[str]] = None
    # Reference to annotations
    annotations: Optional[List[int]] = None
    
    @field_validator('start', 'end', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime strings to datetime objects."""
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                return None
        return v
    
    def get_display_name(self, language: str = 'en') -> str:
        """Get the display name in the specified language, fallback to default name."""
        if self.names:
            return self.names.get(language, self.name)
        return self.name
    
    @property
    def is_time_period(self) -> bool:
        """Check if this value represents a time period."""
        return self.start is not None or self.end is not None
    
    @property
    def time_range_text(self) -> Optional[str]:
        """Get a human-readable time range if this is a time period."""
        if not self.is_time_period:
            return None
        
        if self.start and self.end:
            return f"{self.start.strftime('%Y-%m-%d')} to {self.end.strftime('%Y-%m-%d')}"
        elif self.start:
            return f"From {self.start.strftime('%Y-%m-%d')}"
        elif self.end:
            return f"Until {self.end.strftime('%Y-%m-%d')}"
        return None