from datetime import datetime, date

from pydantic import BaseModel

from statscan.enums.wds.wds_response_status import WDSResponseStatus
from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.subject import Subject
from statscan.enums.auto.wds.survey import Survey

from .footnote import Footnote
from .dimension import Dimension



class BaseCube(BaseModel):
    responseStatusCode: WDSResponseStatus
    productId: int
    cansimId: str
    cubeTitleEn: str
    cubeTitleFr: str
    cubeStartDate: date
    cubeEndDate: date
    
    releaseTime: datetime
    archiveStatusCode: int  # TODO: should be Enum, looks like field can also be named "archived"
    archiveStatusEn: str
    archiveStatusFr: str
    subjectCode: list[Subject]
    surveyCode: list[Survey]
    frequencyCode: Frequency
    corrections: list[int]  # TODO: proper typing required, looks like field can also be named "correctionFootnote" or "correction"
    issueDate: date


class Cube(BaseCube):
    nbSeriesCube: int
    nbDatapointsCube: int
    dimensions: list[Dimension]
    geoAttribute: list  # TODO: proper typing required
