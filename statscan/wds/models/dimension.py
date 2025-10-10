
"""Dimension model and manager for WDS API responses."""

from .base import WDSBaseModel
from .footnote import Footnote
from .link import Link
from .member import Member


class Dimension(WDSBaseModel):
    """Represents a dimension in WDS API responses."""

    dimensionPositionId: int
    dimensionNameEn: str
    dimensionNameFr: str
    hasUom: bool
    member: list[Member]
    footnote: list[Footnote] | None = None
    link: list[Link] | None = None


class DimensionManager:
    """Manages a collection of Dimension objects."""

    def __init__(self, dimensions: list[Dimension]):
        """Initialize manager with a list of dimensions."""
        self._dimensions = dimensions

    @property
    def dimensions(self) -> list[Dimension]:
        """Returns the list of dimensions."""
        return self._dimensions

    def get_dimension(self, dimension_id: int) -> Dimension | None:
        """Get a dimension by its ID."""
        for dimension in self.dimensions:
            if dimension.dimensionPositionId == dimension_id:
                return dimension
        return None

    def get_all_dimensions(self) -> list[Dimension]:
        """Return all dimensions."""
        return self.dimensions
