from pydantic import BaseModel, ConfigDict

from statscan.enums.wds.wds_response_status import WDSResponseStatus
from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.scalar import Scalar
from statscan.enums.auto.wds.uom import UoM

from .datapoint import DataPoint
from .coordinate import Coordinate


class Series(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
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
    memberUomCode: UoM


class ChangedSeriesData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    responseStatusCode: WDSResponseStatus
    productId: int
    coordinate: Coordinate
    vectorId: int
    vectorDataPoint: list[DataPoint]