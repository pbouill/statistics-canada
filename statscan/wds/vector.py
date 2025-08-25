

from pydantic import BaseModel

from statscan.enums.wds.wds_response_status import WDSResponseStatus
from .coordinate import Coordinate
from .datapoint import DataPoint


class Vector(BaseModel):
    responseStatusCode: WDSResponseStatus
    productId: int
    coordinate: Coordinate
    vectorId: int
    vectorDataPoint: list[DataPoint]