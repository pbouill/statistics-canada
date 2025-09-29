from datetime import datetime, date

from pydantic import field_validator

from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.scalar import Scalar
from statscan.enums.auto.wds.symbol import Symbol
from statscan.enums.auto.wds.security_level import SecurityLevel
from statscan.enums.auto.wds.status import Status

from .base import WDSBaseModel


class DataPoint(WDSBaseModel):
    refPer: date | str
    refPer2: date | str | None = None
    refPerRaw: date | str
    refPerRaw2: date | str | None = None
    value: float | int
    decimals: int
    scalarFactorCode: Scalar | int
    symbolCode: Symbol | int
    statusCode: Status | int
    securityLevelCode: SecurityLevel | int
    releaseTime: datetime | str
    frequencyCode: Frequency | int

    @field_validator("refPer2", "refPerRaw2", mode="before")
    @classmethod
    def validate_optional_date_fields(cls, v):
        """Handle empty strings for optional date fields"""
        if v == "" or v is None:
            return None
        return v

    @field_validator("scalarFactorCode", mode="before")
    @classmethod
    def validate_scalar_factor_code(cls, v):
        """Convert integer to Scalar enum if needed"""
        if isinstance(v, int):
            try:
                return Scalar(v)
            except ValueError:
                return v
        return v

    @field_validator("symbolCode", mode="before")
    @classmethod
    def validate_symbol_code(cls, v):
        """Convert integer to Symbol enum if needed"""
        if isinstance(v, int):
            try:
                return Symbol(v)
            except ValueError:
                return v
        return v

    @field_validator("statusCode", mode="before")
    @classmethod
    def validate_status_code(cls, v):
        """Convert integer to Status enum if needed"""
        if isinstance(v, int):
            try:
                return Status(v)
            except ValueError:
                return v
        return v

    @field_validator("securityLevelCode", mode="before")
    @classmethod
    def validate_security_level_code(cls, v):
        """Convert integer to SecurityLevel enum if needed"""
        if isinstance(v, int):
            try:
                return SecurityLevel(v)
            except ValueError:
                return v
        return v

    @field_validator("frequencyCode", mode="before")
    @classmethod
    def validate_frequency_code(cls, v):
        """Convert integer to Frequency enum if needed"""
        if isinstance(v, int):
            try:
                return Frequency(v)
            except ValueError:
                return v
        return v
