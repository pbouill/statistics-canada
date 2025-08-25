from datetime import datetime, date

from pydantic import BaseModel

from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.scalar import Scalar
from statscan.enums.auto.wds.symbol import Symbol
from statscan.enums.auto.wds.security_level import SecurityLevel
from statscan.enums.wds.status import Status


class DataPoint(BaseModel):
    refPer: date
    refPer2: date
    refPerRaw: date
    refPerRaw2: date
    value: float | int
    decimals: int
    scalarFactorCode: Scalar
    symbolCode: Symbol
    statusCode: Status
    securityLevelCode: SecurityLevel
    releaseTime: datetime
    frequencyCode: Frequency