from datetime import datetime, date
from typing import Optional, Any

from pydantic import field_validator, model_validator, Field

from statscan.enums.wds.wds_response_status import WDSResponseStatus
from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.subject import Subject
from statscan.enums.auto.wds.survey import Survey
from statscan.enums.auto.wds.status import Status

from .base import WDSBaseModel
from .footnote import Footnote
from .dimension import Dimension
from .correction import Correction



class CubeExistsError(ValueError):
    pass


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
    archiveStatusCode: Optional[Status | int | str] = None  # API returns string, model expects int
    archiveStatusEn: Optional[str] = None
    archiveStatusFr: Optional[str] = None
    subjectCode: Optional[list[Subject | int | str]] = None  # API returns list of strings
    surveyCode: Optional[list[Survey | int | str]] = None  # API returns list of strings  
    frequencyCode: Frequency | int  # API may return int
    correction: Optional[list[Correction]] = None  # API field name
    correctionFootnote: Optional[list[Correction]] = None  # API field name  
    issueDate: Optional[datetime] = None

    # full cube attributes
    nbSeriesCube: Optional[int] = None
    nbDatapointsCube: Optional[int] = None
    dimensions: Optional[list[Dimension]] = Field(None, alias="dimension")  # API uses singular "dimension"
    geoAttribute: Optional[list] = None  # TODO: proper typing required

    @field_validator("productId", mode="before")
    @classmethod
    def convert_product_id_to_int(cls, v: Any) -> int:
        """Convert productId from string to int"""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator("archiveStatusCode", mode="before")
    @classmethod
    def convert_archive_status_to_int(cls, v: Any) -> Optional[int]:
        """Convert archiveStatusCode from string to int"""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator("subjectCode", "surveyCode", mode="before")
    @classmethod
    def convert_str_list_to_int_list(cls, v: Any) -> Optional[list[int]]:
        """
        Takes the incoming list of string numbers and converts each
        element to an integer before standard validation runs.
        """
        if v is None:
            return None
        if isinstance(v, list):
            return [int(item) for item in v]
        return v

    @field_validator("cubeStartDate", "cubeEndDate", "releaseTime", "issueDate", mode="before")
    @classmethod
    def convert_date_strings(cls, v: Any) -> Optional[datetime]:
        """Convert date strings to datetime objects"""
        if v is None:
            return None
        if isinstance(v, str):
            # Handle different date formats from API
            if 'T' in v:
                # "2022-02-09T08:30" format
                return datetime.fromisoformat(v)
            else:
                # "2021-01-01" format
                return datetime.fromisoformat(f"{v}T00:00:00")
        return v

    @property 
    def corrections(self) -> list[Correction]:
        """Combined corrections from both API fields"""
        result = []
        if self.correction:
            result.extend(self.correction)
        if self.correctionFootnote:
            result.extend(self.correctionFootnote)
        return result


