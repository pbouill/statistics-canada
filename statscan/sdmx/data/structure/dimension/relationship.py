"""SDMX dimension relationship models."""

from ....base import Base


class Relationship(Base):
    """Represents relationships between dimensions."""

    dimensions: list[str]
