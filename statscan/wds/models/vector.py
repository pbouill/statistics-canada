"""Vector data model for WDS API responses."""

from pydantic import ConfigDict

from statscan.enums.wds.wds_response_status import WDSResponseStatus

from ..coordinate import Coordinate
from .base import WDSBaseModel
from .datapoint import DataPoint


class Vector(WDSBaseModel):
    """Represents a vector with coordinate and data points from the WDS API."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    responseStatusCode: WDSResponseStatus
    productId: int
    coordinate: Coordinate
    vectorId: int
    vectorDataPoint: list[DataPoint]
