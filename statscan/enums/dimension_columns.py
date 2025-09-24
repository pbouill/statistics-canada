"""
Enums for census data dimension columns and metadata.

This module provides enum definitions for standardizing column names
and dimension identifiers in census datasets.
"""

from enum import Enum, StrEnum
from typing import Optional


class DimensionColumn(StrEnum):
    """Standard dimension column names in census datasets."""
    GENDER = "Gender"
    CENSUS_PROFILE_CHARACTERISTIC = "Census Profile Characteristic"
    STATISTIC_TYPE = "Statistic Type"
    GEOGRAPHY = "Geography"
    GEOGRAPHIC_LEVEL = "Geographic Level"
    UOM = "UOM"  # Unit of Measure
    UOM_ID = "UOM_ID"
    SCALAR_FACTOR = "Scalar Factor"
    SCALAR_ID = "SCALAR_ID"
    VECTOR = "Vector"
    COORDINATE = "Coordinate"
    
    @property
    def description(self) -> str:
        """Get description of the dimension column."""
        descriptions = {
            DimensionColumn.GENDER: "Gender dimension (Male, Female, Total)",
            DimensionColumn.CENSUS_PROFILE_CHARACTERISTIC: "Census characteristic being measured",
            DimensionColumn.STATISTIC_TYPE: "Type of statistic (count, percentage, rate, etc.)",
            DimensionColumn.GEOGRAPHY: "Geographic area name",
            DimensionColumn.GEOGRAPHIC_LEVEL: "Level of geographic aggregation",
            DimensionColumn.UOM: "Unit of measurement description",
            DimensionColumn.UOM_ID: "Unit of measurement identifier",
            DimensionColumn.SCALAR_FACTOR: "Scaling factor for values",
            DimensionColumn.SCALAR_ID: "Scaling factor identifier",
            DimensionColumn.VECTOR: "Vector identifier for the dataset",
            DimensionColumn.COORDINATE: "Coordinate within the data structure"
        }
        return descriptions.get(self, f"Dimension: {self.value}")


class MetadataColumn(StrEnum):
    """Standard metadata column names in census datasets."""
    SERIES_KEY = "series_key"
    TIME_PERIOD = "time_period"
    VALUE = "value"
    DGUID = "DGUID"
    STATUS = "STATUS"
    SYMBOL = "SYMBOL"
    TERMINATED = "TERMINATED"
    DECIMALS = "DECIMALS"
    
    @property
    def description(self) -> str:
        """Get description of the metadata column."""
        descriptions = {
            MetadataColumn.SERIES_KEY: "Unique identifier for the data series",
            MetadataColumn.TIME_PERIOD: "Time period for the observation",
            MetadataColumn.VALUE: "The actual data value",
            MetadataColumn.DGUID: "Data Geographic Unique Identifier",
            MetadataColumn.STATUS: "Status of the data point",
            MetadataColumn.SYMBOL: "Symbol indicating data quality or type",
            MetadataColumn.TERMINATED: "Whether the series is terminated",
            MetadataColumn.DECIMALS: "Number of decimal places for the value"
        }
        return descriptions.get(self, f"Metadata: {self.value}")


class SeriesKeyPosition(Enum):
    """Positions within series keys for different dimensions."""
    GENDER = 0
    CHARACTERISTIC = 1
    STATISTIC_TYPE = 2
    GEOGRAPHY = 3
    UOM = 4
    SCALAR = 5
    
    @property
    def column_name(self) -> str:
        """Get the corresponding dimension column name."""
        mapping = {
            SeriesKeyPosition.GENDER: DimensionColumn.GENDER,
            SeriesKeyPosition.CHARACTERISTIC: DimensionColumn.CENSUS_PROFILE_CHARACTERISTIC,
            SeriesKeyPosition.STATISTIC_TYPE: DimensionColumn.STATISTIC_TYPE,
            SeriesKeyPosition.GEOGRAPHY: DimensionColumn.GEOGRAPHY,
            SeriesKeyPosition.UOM: DimensionColumn.UOM_ID,
            SeriesKeyPosition.SCALAR: DimensionColumn.SCALAR_ID
        }
        return mapping.get(self, f"series_key_dim_{self.value}")


class ColumnType(Enum):
    """Types of columns in census datasets."""
    DIMENSION = "dimension"
    METADATA = "metadata"
    SERIES_KEY_COMPONENT = "series_key_component"
    DERIVED = "derived"
    
    @property
    def description(self) -> str:
        descriptions = {
            ColumnType.DIMENSION: "Dimension that defines data categorization",
            ColumnType.METADATA: "Metadata about the data points",
            ColumnType.SERIES_KEY_COMPONENT: "Component extracted from series key",
            ColumnType.DERIVED: "Derived or calculated column"
        }
        return descriptions.get(self, "Unknown column type")


class ValueType(Enum):
    """Types of values that can appear in census data."""
    NUMERIC = "numeric"
    TEXT = "text"
    CODE = "code"
    MISSING = "missing"
    NOT_AVAILABLE = "not_available"
    CONFIDENTIAL = "confidential"
    
    @classmethod
    def from_value(cls, value) -> 'ValueType':
        """Determine value type from actual value."""
        if value is None or str(value).strip() == '':
            return cls.MISSING
        
        str_value = str(value).strip().upper()
        
        # Check for special codes
        if str_value in ['..', '...', 'X', 'F']:
            return cls.CONFIDENTIAL
        elif str_value in ['0', '.']:
            return cls.NOT_AVAILABLE
        
        # Try to convert to numeric
        try:
            float(value)
            return cls.NUMERIC
        except (ValueError, TypeError):
            # Check if it's a code pattern (mostly digits/letters)
            if len(str_value) <= 10 and any(c.isdigit() for c in str_value):
                return cls.CODE
            return cls.TEXT
