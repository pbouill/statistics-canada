from pydantic import BaseModel


class Link(BaseModel):
    footnoteId: int
    dimensionPositionId: int
    memberId: int