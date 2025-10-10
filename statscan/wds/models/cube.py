
"""Cube model and error for WDS API responses."""

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.status import Status
from statscan.enums.auto.wds.subject import Subject
from statscan.enums.auto.wds.survey import Survey
from statscan.enums.wds.wds_response_status import WDSResponseStatus

from .base import WDSBaseModel
from .correction import Correction
from .dimension import Dimension


class CubeExistsError(ValueError):
    """Raised when a Cube with the same productId already exists."""

    pass


class Cube(WDSBaseModel):
    """Represents a Cube object in WDS API responses."""

    # base cube (lite) attributes
    responseStatusCode: WDSResponseStatus | None = None
    productId: int
    cansimId: str | None = None
    cubeTitleEn: str
    cubeTitleFr: str
    cubeStartDate: datetime
    cubeEndDate: datetime

    releaseTime: datetime
    archiveStatusCode: Status | int | str | None = (
        None  # API returns string, model expects int
    )
    archiveStatusEn: str | None = None
    archiveStatusFr: str | None = None
    subjectCode: list[Subject | int | str] | None = (
        None  # API returns list of strings
    )
    surveyCode: list[Survey | int | str] | None = None  # API returns list of strings
    frequencyCode: Frequency | int  # API may return int
    correction: list[Correction] | None = None  # API field name
    correctionFootnote: list[Correction] | None = None  # API field name
    issueDate: datetime | None = None

    # full cube attributes
    nbSeriesCube: int | None = None
    nbDatapointsCube: int | None = None
    dimensions: list[Dimension] | None = Field(
        None, alias="dimension"
    )  # API uses singular "dimension"
    geoAttribute: list | None = None  # TODO: proper typing required

    @field_validator("productId", mode="before")
    @classmethod
    def convert_product_id_to_int(cls, v: Any) -> int:
        """Convert productId from string to int."""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator("archiveStatusCode", mode="before")
    @classmethod
    def convert_archive_status_to_int(cls, v: Any) -> int | None:
        """Convert archiveStatusCode from string to int."""
        if isinstance(v, str):
            return int(v)
        return v

    @field_validator("subjectCode", "surveyCode", mode="before")
    @classmethod
    def convert_str_list_to_int_list(cls, v: Any) -> list[int] | None:
        """Convert incoming list of string numbers to integers.

        Processes the list before standard validation runs.

        """
        if v is None:
            return None
        if isinstance(v, list):
            return [int(item) for item in v]
        return v

    @field_validator(
        "cubeStartDate", "cubeEndDate", "releaseTime", "issueDate", mode="before"
    )
    @classmethod
    def convert_date_strings(cls, v: Any) -> datetime | None:
        """Convert date strings to datetime objects."""
        if v is None:
            return None
        if isinstance(v, str):
            # Handle different date formats from API
            if "T" in v:
                # "2022-02-09T08:30" format
                return datetime.fromisoformat(v)
            else:
                # "2021-01-01" format
                return datetime.fromisoformat(f"{v}T00:00:00")
        return v

    @property
    def corrections(self) -> list[Correction]:
        """Combined corrections from both API fields."""
        result = []
        if self.correction:
            result.extend(self.correction)
        if self.correctionFootnote:
            result.extend(self.correctionFootnote)
        return result
