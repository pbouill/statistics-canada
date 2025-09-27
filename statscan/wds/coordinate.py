#!/usr/bin/env python3
"""
WDS Coordinate System

This module provides a unified, enhanced Coordinate class for the Statistics Canada WDS API.
The Coordinate class integrates:
- Pydantic model compatibility for WDS API responses
- Advanced parameter mapping to dimension members
- Interactive coordinate building from dimension parameters
- Enhanced DataFrame creation with enum-based columns
"""

from dataclasses import dataclass
from typing import Any, Generator, Optional
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
import pandas as pd

from .models.member import Member, MemberManager
from .models.dimension import DimensionManager
from statscan.enums.auto.wds.status import Status
from statscan.enums.auto.wds.symbol import Symbol
from statscan.enums.auto.wds.scalar import Scalar


@dataclass
class CoordinateParameter:
    """Represents a single coordinate parameter with its dimension context."""

    dimension_position: int
    dimension_name: str
    member_id: int
    member_name: str

    def __str__(self) -> str:
        return f"{self.dimension_name}: {self.member_name} (ID: {self.member_id})"


class Coordinate:
    """
    Enhanced coordinate class for WDS API integration with Pydantic models.

    Provides both basic coordinate functionality and advanced interactive features:
    - Pydantic model integration for WDS API responses
    - Parameter mapping to dimension members
    - Interactive coordinate building from dimension parameters
    - Human-readable descriptions and parameter access
    """

    def __init__(
        self,
        coord_str: str,
        member_manager: Optional[MemberManager] = None,
        dimension_manager: Optional[DimensionManager] = None,
    ):
        self.__coord_str = coord_str
        self.member_manager = member_manager
        self.dimension_manager = dimension_manager
        self._parameters: list[CoordinateParameter] | None = None

    @property
    def member_ids(self) -> list[int]:
        """Get the raw member IDs from the coordinate string."""
        return [int(m) for m in str(self).split(".")]

    @property
    def coordinate_string(self) -> str:
        """Get the coordinate string (alias for backward compatibility)."""
        return self.__coord_str

    @property
    def parameters(self) -> list[CoordinateParameter]:
        """Get the coordinate parameters with dimension context."""
        if self._parameters is None:
            self._parameters = self._build_parameters()
        return self._parameters

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """
        Defines the Pydantic V2 Core Schema for the Coordinate class.

        This schema tells Pydantic to:
        1.  Expect a string as input.
        2.  Call this class's constructor (`__init__`) with the string to validate it and create an instance.
        3.  Also allow instances of `Coordinate` to pass through validation unmodified.
        """
        # This validator function will be called with the input string
        # and should return an instance of Coordinate.
        from_str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=core_schema.union_schema(
                [core_schema.is_instance_schema(cls), from_str_schema]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    def __getitem__(self, idx) -> Member:
        if self.member_manager is None:
            raise ValueError("MemberManager is not set.")
        return self.member_manager[self.member_ids[idx]]

    def __iter__(self) -> Generator[Member, Any, None]:
        if self.member_manager is None:
            raise ValueError("MemberManager is not set.")
        for member_id in self.member_ids:
            yield self.member_manager[member_id]

    def __str__(self):
        return self.__coord_str

    # Enhanced Interactive Features

    def _build_parameters(self) -> list[CoordinateParameter]:
        """Build parameter objects from coordinate and dimensions."""
        if not self.dimension_manager:
            # Return basic parameters without dimension context
            member_ids = self.member_ids
            return [
                CoordinateParameter(
                    dimension_position=i + 1,
                    dimension_name=f"Dimension {i + 1}",
                    member_id=member_id,
                    member_name=f"Member {member_id}",
                )
                for i, member_id in enumerate(member_ids)
            ]

        parameters = []
        member_ids = self.member_ids

        for i, member_id in enumerate(member_ids):
            dimension_position = i + 1
            dimension = self.dimension_manager.get_dimension(dimension_position)

            if dimension and member_id != 0:
                # Find the member in this dimension
                member_name = f"Member {member_id}"  # Default
                if dimension.member:
                    for member in dimension.member:
                        if member.memberId == member_id:
                            member_name = member.memberNameEn
                            break

                parameters.append(
                    CoordinateParameter(
                        dimension_position=dimension_position,
                        dimension_name=dimension.dimensionNameEn,
                        member_id=member_id,
                        member_name=member_name,
                    )
                )
            else:
                # Dimension not found or member_id is 0 (unused dimension)
                if member_id != 0:
                    parameters.append(
                        CoordinateParameter(
                            dimension_position=dimension_position,
                            dimension_name=f"Unknown Dimension {dimension_position}",
                            member_id=member_id,
                            member_name=f"Member {member_id}",
                        )
                    )

        return parameters

    def get_parameter_by_dimension_name(
        self, dimension_name: str
    ) -> CoordinateParameter | None:
        """Get a parameter by dimension name (case-insensitive)."""
        for param in self.parameters:
            if dimension_name.lower() in param.dimension_name.lower():
                return param
        return None

    def get_parameter_by_position(self, position: int) -> CoordinateParameter | None:
        """Get a parameter by dimension position."""
        for param in self.parameters:
            if param.dimension_position == position:
                return param
        return None

    def describe(self) -> str:
        """Get a human-readable description of the coordinate."""
        if not self.parameters:
            return f"Coordinate: {self.coordinate_string}"

        descriptions = []
        for param in self.parameters:
            descriptions.append(str(param))

        return f"Coordinate {self.coordinate_string}:\n  " + "\n  ".join(descriptions)

    @classmethod
    def build_from_parameters(
        cls,
        dimension_manager: DimensionManager,
        **dimension_values: dict[str, str | int],
    ) -> "Coordinate":
        """
        Build a coordinate from dimension parameters.

        Args:
            dimension_manager: Manager with dimension metadata
            **dimension_values: Dimension name -> member name/ID mappings

        Example:
            coord = Coordinate.build_from_parameters(
                dim_manager,
                Geography="Canada",
                Gender="Men+",
                Age="Total - Age"
            )
        """
        member_ids = [0] * 10  # Default WDS coordinate length

        # Map dimension values to member IDs
        for dim_name, value in dimension_values.items():
            dimension = None

            # Find dimension by name (case-insensitive)
            for dim in dimension_manager.dimensions:
                if dim_name.lower() in dim.dimensionNameEn.lower():
                    dimension = dim
                    break

            if not dimension:
                raise ValueError(f"Dimension '{dim_name}' not found")

            # Find member by name or ID
            member_id = None
            if isinstance(value, int):
                member_id = value
            else:
                # Search by name
                value_str = str(value).lower()
                if dimension.member:
                    for member in dimension.member:
                        if value_str in member.memberNameEn.lower():
                            member_id = member.memberId
                            break

            if member_id is None:
                raise ValueError(
                    f"Member '{value}' not found in dimension '{dim_name}'"
                )

            # Set the member ID at the correct position
            position_idx = dimension.dimensionPositionId - 1
            if 0 <= position_idx < len(member_ids):
                member_ids[position_idx] = member_id

        coordinate_string = ".".join(str(mid) for mid in member_ids)
        return cls(coordinate_string, dimension_manager=dimension_manager)

    # DataFrame Creation Methods

    @classmethod
    def create_demographic_dataframe(
        cls,
        data_points: list[Any],
        coordinates: list["Coordinate"],
        product_id: int,
        demographic_type: str,
        geographic_name: str,
        census_year: int = 2021,
    ) -> pd.DataFrame:
        """
        Create a clean demographic DataFrame using enums and coordinates.

        Args:
            data_points: List of WDS data points with values and metadata
            coordinates: List of Coordinate objects
            product_id: WDS product ID
            demographic_type: Type of demographic data
            geographic_name: Name of the geographic area
            census_year: Census year

        Returns:
            Clean pandas DataFrame with consistent enum-based columns
        """
        records = []

        for i, (dp, coord) in enumerate(zip(data_points, coordinates)):
            if not dp or not coord:
                continue

            # Extract coordinate parameters for cleaner column values
            geography_param = coord.get_parameter_by_dimension_name("Geography")
            year_param = coord.get_parameter_by_dimension_name(
                "Census year"
            ) or coord.get_parameter_by_position(2)
            characteristic_param = coord.get_parameter_by_position(
                3
            )  # Usually age/demographic characteristic
            gender_param = coord.get_parameter_by_dimension_name(
                "Gender"
            ) or coord.get_parameter_by_position(4)

            # Use enum values consistently
            status_enum = None
            status_description = "Unknown"
            if hasattr(dp, "statusCode") and dp.statusCode:
                try:
                    status_enum = (
                        Status(dp.statusCode)
                        if isinstance(dp.statusCode, int)
                        else dp.statusCode
                    )
                    status_description = status_enum.name.replace("_", " ").title()
                except (ValueError, AttributeError):
                    status_description = f"Status Code {dp.statusCode}"

            symbol_enum = None
            symbol_description = None
            if hasattr(dp, "symbolCode") and dp.symbolCode:
                try:
                    symbol_enum = (
                        Symbol(dp.symbolCode)
                        if isinstance(dp.symbolCode, int)
                        else dp.symbolCode
                    )
                    if symbol_enum != Symbol.NONE:
                        symbol_description = symbol_enum.name.replace("_", " ").title()
                except (ValueError, AttributeError):
                    symbol_description = f"Symbol Code {dp.symbolCode}"

            scalar_enum = None
            scalar_description = None
            if hasattr(dp, "scalarFactorCode") and dp.scalarFactorCode:
                try:
                    scalar_enum = (
                        Scalar(dp.scalarFactorCode)
                        if isinstance(dp.scalarFactorCode, int)
                        else dp.scalarFactorCode
                    )
                    scalar_description = scalar_enum.name.replace("_", " ").title()
                except (ValueError, AttributeError):
                    scalar_description = f"Scalar Code {dp.scalarFactorCode}"

            # Build clean record
            record = {
                # Core identifiers
                "product_id": product_id,
                "demographic_type": demographic_type,
                "geographic_name": geographic_name,
                "census_year": census_year,
                # Coordinate breakdown (clean parameter names)
                "geography": geography_param.member_name
                if geography_param
                else "Unknown",
                "year_period": year_param.member_name
                if year_param
                else str(census_year),
                "characteristic": characteristic_param.member_name
                if characteristic_param
                else "Unknown",
                "gender": gender_param.member_name if gender_param else "Total",
                # Data value
                "value": float(dp.value)
                if hasattr(dp, "value") and dp.value is not None
                else None,
                # Quality indicators (using enums)
                "status_code": status_enum.value if status_enum else None,
                "status": status_description,
                "symbol_code": symbol_enum.value if symbol_enum else None,
                "symbol": symbol_description,
                "scalar_code": scalar_enum.value if scalar_enum else None,
                "scalar": scalar_description,
                # Metadata
                "coordinate": coord.coordinate_string,
                "ref_date": getattr(dp, "refPer", None),
                "release_time": getattr(dp, "releaseTime", None),
                # Quality assessment (human-readable)
                "data_quality": cls._assess_data_quality(dp, status_enum, symbol_enum),
            }

            records.append(record)

        return pd.DataFrame(records)

    @classmethod
    def _assess_data_quality(
        cls, data_point: Any, status_enum: Status | None, symbol_enum: Symbol | None
    ) -> str:
        """Assess data quality with human-readable description."""
        if not hasattr(data_point, "value") or data_point.value is None:
            return "❌ No Data"

        if status_enum:
            if status_enum == Status.NORMAL:
                return "✅ Excellent"
            elif status_enum == Status.DATA_QUAL_EXCELLENT:
                return "✅ Excellent Quality"
            elif status_enum == Status.DATA_QUAL_VERY_GOOD:
                return "🟢 Very Good Quality"
            elif status_enum == Status.DATA_QUAL_GOOD:
                return "🟡 Good Quality"
            elif status_enum == Status.DATA_QUAL_ACCEPT:
                return "🟠 Acceptable Quality"
            elif status_enum == Status.USE_WITH_CAUTION:
                return "🔶 Use With Caution"
            elif status_enum == Status.TOO_UNRELIABLE_TO_BE_PUB:
                return "🔴 Too Unreliable"

        if symbol_enum and symbol_enum != Symbol.NONE:
            return f"⚠️ {symbol_enum.name.replace('_', ' ').title()}"

        return "✅ Normal"

    @classmethod
    async def create_enhanced_demographic_dataframe(
        cls,
        entity_member_id: int,
        entity_name: str,
        product_id: int,
        demographic_type: str,
        client,  # WDS client
        census_year: int = 2021,
        max_characteristics: int = 20,
    ) -> pd.DataFrame:
        """
        Create an enhanced demographic DataFrame with coordinates and enum-based columns.

        This is a complete demographic DataFrame creation method that uses:
        - Unified coordinate system
        - Consistent enum-based status/symbol/scalar columns
        - Clean parameter-based column names
        - Better data quality assessment
        """
        try:
            # Get cube metadata to understand dimensions
            cube = await client.get_cube_metadata(product_id)

            if not cube.dimensions or len(cube.dimensions) < 3:
                return pd.DataFrame(
                    [
                        {
                            "error": f"Insufficient dimensions in product {product_id}",
                            "product_id": product_id,
                            "demographic_type": demographic_type,
                        }
                    ]
                )

            # Create dimension manager
            from .models.dimension import DimensionManager

            dim_manager = DimensionManager(cube.dimensions)

            # Build coordinates and retrieve data
            coordinates = []
            data_points = []

            # Find key dimensions
            year_dim = cube.dimensions[1] if len(cube.dimensions) > 1 else None
            char_dim = cube.dimensions[2] if len(cube.dimensions) > 2 else None
            gender_dim = cube.dimensions[3] if len(cube.dimensions) > 3 else None

            # Find census year member ID
            year_member_id = 1  # Default
            if year_dim and year_dim.member:
                for member in year_dim.member:
                    if str(census_year) in member.memberNameEn:
                        year_member_id = member.memberId
                        break

            # Process characteristics (limit for performance)
            if char_dim and char_dim.member:
                for char_member in char_dim.member[:max_characteristics]:
                    if gender_dim and gender_dim.member:
                        # Process each gender
                        for gender_member in gender_dim.member:
                            coord_string = f"{entity_member_id}.{year_member_id}.{char_member.memberId}.{gender_member.memberId}.0.0.0.0.0.0"
                            coord = cls(coord_string, dimension_manager=dim_manager)

                            try:
                                data_result = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
                                    product_id=product_id, coordinate=coord_string, n=1
                                )

                                if (
                                    hasattr(data_result, "vectorDataPoint")
                                    and data_result.vectorDataPoint
                                    and len(data_result.vectorDataPoint) > 0
                                ):
                                    coordinates.append(coord)
                                    data_points.append(data_result.vectorDataPoint[0])

                            except Exception:
                                # Skip failed coordinates
                                continue
                    else:
                        # No gender dimension
                        coord_string = f"{entity_member_id}.{year_member_id}.{char_member.memberId}.0.0.0.0.0.0.0"
                        coord = cls(coord_string, dimension_manager=dim_manager)

                        try:
                            data_result = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
                                product_id=product_id, coordinate=coord_string, n=1
                            )

                            if (
                                hasattr(data_result, "vectorDataPoint")
                                and data_result.vectorDataPoint
                                and len(data_result.vectorDataPoint) > 0
                            ):
                                coordinates.append(coord)
                                data_points.append(data_result.vectorDataPoint[0])

                        except Exception:
                            continue

            # Create enhanced DataFrame using the class method
            if coordinates and data_points:
                return cls.create_demographic_dataframe(
                    data_points=data_points,
                    coordinates=coordinates,
                    product_id=product_id,
                    demographic_type=demographic_type,
                    geographic_name=entity_name,
                    census_year=census_year,
                )
            else:
                return pd.DataFrame(
                    [
                        {
                            "error": "No valid data coordinates found",
                            "product_id": product_id,
                            "demographic_type": demographic_type,
                            "geographic_name": entity_name,
                        }
                    ]
                )

        except Exception as e:
            return pd.DataFrame(
                [
                    {
                        "error": f"Enhanced DataFrame creation failed: {str(e)[:100]}",
                        "product_id": product_id,
                        "demographic_type": demographic_type,
                        "geographic_name": entity_name,
                    }
                ]
            )


# Backward compatibility aliases for existing imports
class EnhancedDataFrameBuilder:
    """
    Deprecated: DataFrame creation methods are now available as Coordinate class methods.
    Use Coordinate.create_demographic_dataframe() instead.
    """

    @staticmethod
    def create_demographic_dataframe(*args, **kwargs):
        """Deprecated: Use Coordinate.create_demographic_dataframe() instead."""
        return Coordinate.create_demographic_dataframe(*args, **kwargs)

    @staticmethod
    def _assess_data_quality(*args, **kwargs):
        """Deprecated: Use Coordinate._assess_data_quality() instead."""
        return Coordinate._assess_data_quality(*args, **kwargs)


# Backward compatibility function
async def create_enhanced_demographic_dataframe(*args, **kwargs):
    """
    Deprecated: Use Coordinate.create_enhanced_demographic_dataframe() instead.
    This function is maintained for backward compatibility.
    """
    return await Coordinate.create_enhanced_demographic_dataframe(*args, **kwargs)
