# from pydantic import BaseModel
from .base import WDSBaseModel


class Footnote(WDSBaseModel):
    footnoteId: int
    footnotesEn: str
    footnotesFr: str