
"""Footnote model for WDS API responses."""

from .base import WDSBaseModel


class Footnote(WDSBaseModel):
    """Represents a footnote in WDS API responses."""

    footnoteId: int
    footnotesEn: str
    footnotesFr: str
