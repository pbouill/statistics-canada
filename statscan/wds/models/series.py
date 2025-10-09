"""Series data models for WDS API responses."""

# from pydantic import BaseModel, ConfigDict

from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.scalar import Scalar
from statscan.enums.auto.wds.uom import Uom
from statscan.enums.wds.wds_response_status import WDSResponseStatus

from ..coordinate import Coordinate
from .base import WDSBaseModel
from .datapoint import DataPoint


class Series(WDSBaseModel):
    """Represents a data series with metadata from the WDS API."""

    # model_config = ConfigDict(arbitrary_types_allowed=True)

    responseStatusCode: WDSResponseStatus
    productId: int
    coordinate: Coordinate
    vectorId: int
    frequencyCode: Frequency
    scalarFactorCode: Scalar
    decimals: int
    terminated: bool
    SeriesTitleEn: str
    SeriesTitleFr: str
    memberUomCode: Uom


class ChangedSeriesData(WDSBaseModel):
    """Represents changed series data with vector data points."""

    # model_config = ConfigDict(arbitrary_types_allowed=True)

    responseStatusCode: WDSResponseStatus
    productId: int
    coordinate: Coordinate
    vectorId: int
    vectorDataPoint: list[DataPoint]
