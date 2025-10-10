
"""Link model for WDS API responses."""

from .base import WDSBaseModel


class Link(WDSBaseModel):
    """Represents a link between dimensions and members in WDS API responses."""

    footnoteId: int
    dimensionPositionId: int
    memberId: int
