from datetime import datetime

from .base import WDSBaseModel


class Correction(WDSBaseModel):
    correctionDate: datetime
    correctionNoteEn: str
    correctionNoteFr: str
