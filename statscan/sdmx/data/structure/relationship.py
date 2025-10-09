"""SDMX relationship models for dimension and attribute connections."""

from ...base import Base


class Relationship(Base):
    """Represents a relationship between dimensions or attributes in SDMX."""

    dimensions: list[str] | None = None
    observation: dict | None = None
    primaryMeasure: str | None = None  # noqa: N815

    def has_dimension_relationship(self) -> bool:
        """Check if this relationship has dimension relationships."""
        return self.dimensions is not None and len(self.dimensions) > 0

    def has_observation_relationship(self) -> bool:
        """Check if this relationship has observation relationships."""
        return self.observation is not None
