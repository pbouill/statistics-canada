from pydantic import ConfigDict

from statscan.enums.wds.wds_response_status import WDSResponseStatus

from .base import WDSBaseModel
from ..coordinate import Coordinate
from .datapoint import DataPoint


class Vector(WDSBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    responseStatusCode: WDSResponseStatus
    productId: int
    coordinate: Coordinate
    vectorId: int
    vectorDataPoint: list[DataPoint]
