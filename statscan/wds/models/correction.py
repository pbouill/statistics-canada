"""Correction model for WDS API responses."""

from datetime import datetime

from .base import WDSBaseModel


class Correction(WDSBaseModel):
    """Represents a correction entry in WDS API responses."""

    correctionDate: datetime
    correctionNoteEn: str
    correctionNoteFr: str
