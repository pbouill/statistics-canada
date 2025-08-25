from pydantic import BaseModel


class Footnote(BaseModel):
    footnoteId: int
    footnotesEn: str
    footnotesFr: str