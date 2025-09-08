from datetime import datetime, date
from typing import Optional, Any

from pydantic import field_validator

from statscan.enums.wds.wds_response_status import WDSResponseStatus
from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.subject import Subject
from statscan.enums.auto.wds.survey import Survey
from statscan.enums.auto.wds.status import Status

from .base import WDSBaseModel
from .footnote import Footnote
from .dimension import Dimension
from .correction import Correction


class Cube(WDSBaseModel):
    # base cube (lite) attributes
    responseStatusCode: Optional[WDSResponseStatus] = None
    productId: int
    cansimId: Optional[str] = None
    cubeTitleEn: str
    cubeTitleFr: str
    cubeStartDate: datetime
    cubeEndDate: datetime

    releaseTime: datetime
    archiveStatusCode: Optional[Status] = None  # TODO: should be Enum, looks like field can also be named "archived"
    archiveStatusEn: Optional[str] = None
    archiveStatusFr: Optional[str] = None
    subjectCode: Optional[list[Subject]]
    surveyCode: Optional[list[Survey]] = None
    frequencyCode: Frequency
    corrections: list[Correction]  # TODO: proper typing required, looks like field can also be named "correctionFootnote" or "correction"
    issueDate: Optional[datetime] = None

    # full cube attributes
    nbSeriesCube: Optional[int] = None
    nbDatapointsCube: Optional[int] = None
    dimensions: Optional[list[Dimension]] = None
    geoAttribute: Optional[list] = None  # TODO: proper typing required

    @field_validator("subjectCode", "surveyCode", mode="before")
    @classmethod
    def convert_str_list_to_int_list(cls, v: Any) -> list[int]:
        """
        Takes the incoming list of string numbers and converts each
        element to an integer before standard validation runs.
        """
        if isinstance(v, list):
            # This list comprehension is the intermediary step you need
            return [int(item) for item in v]
        return v
