# from pydantic import BaseModel
from .base import WDSBaseModel


class Link(WDSBaseModel):
    footnoteId: int
    dimensionPositionId: int
    memberId: int