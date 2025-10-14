
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

    def get_dimension(self, dimension_id: int) -> Dimension | None:
        """Get a dimension by its position ID.

        Args:
            dimension_id: The dimension position ID to search for.

        Returns:
            The Dimension object if found, None otherwise.

        """
        if not self.dimensions:
            return None
        for dimension in self.dimensions:
            if dimension.dimensionPositionId == dimension_id:
                return dimension
        return None

    def build_coordinate(self, **dimension_values: str | int):
        """Build a Coordinate object from dimension parameters.

        Provides a convenient way to build coordinates directly from cube metadata
        without manually creating a DimensionManager. Returns a full Coordinate
        object with rich metadata access.

        Args:
            **dimension_values: Keyword arguments mapping dimension names to
                member names or IDs (e.g., Geography="Canada", Gender="Men+")

        Returns:
            A Coordinate object with dimension context, allowing access to
            coordinate parameters, descriptions, and metadata.

        Raises:
            ValueError: If dimensions are not available, dimension name not found,
                or member value not found.
            ImportError: If coordinate module cannot be imported.

        Example:
            >>> cube = await client.get_cube_metadata(98100001)
            >>> coord = cube.build_coordinate(Geographic="Canada")
            >>> print(coord.describe())  # Human-readable description
            >>> print(coord.coordinate_string)  # "1.0.0.0.0.0.0.0.0.0"
            >>> # Use with client methods (Coordinate converts to string)
            >>> data = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
            ...     product_id=98100001, coordinate=coord, n=1
            ... )

        """
        if not self.dimensions:
            raise ValueError(
                f"Cube {self.productId} does not have dimension metadata loaded"
            )

        try:
            from statscan.wds.coordinate import Coordinate  # noqa: PLC0415
            from statscan.wds.models.dimension import DimensionManager  # noqa: PLC0415
        except ImportError as e:
            raise ImportError(
                "Failed to import coordinate building dependencies"
            ) from e

        # Create temporary DimensionManager for coordinate building
        dim_manager = DimensionManager(self.dimensions)
        coord_obj = Coordinate.build_from_parameters(dim_manager, **dimension_values)
        return coord_obj

    def validate_coordinate(self, coordinate: str | Any) -> tuple[bool, str]:
        """Validate a coordinate string against this cube's dimensions.

        Checks if the coordinate has valid structure and member IDs that exist
        in the cube's dimensions.

        Args:
            coordinate: The coordinate string (e.g., "1.2.3.0.0.0.0.0.0.0")
                or Coordinate object to validate.

        Returns:
            A tuple of (is_valid, error_message). If valid, error_message is empty.

        Example:
            >>> cube = await client.get_cube_metadata(98100001)
            >>> is_valid, error = cube.validate_coordinate("1.2.3.0.0.0.0.0.0.0")
            >>> if not is_valid:
            ...     print(f"Invalid coordinate: {error}")

        """
        if not self.dimensions:
            return False, f"Cube {self.productId} has no dimension metadata"

        # Convert Coordinate object to string
        coord_str = str(coordinate)

        # Parse coordinate string
        try:
            member_ids = [int(x) for x in coord_str.split(".")]
        except (ValueError, AttributeError) as e:
            return False, f"Invalid coordinate format: {e}"

        # Check length matches dimension count
        expected_length = len(self.dimensions)
        if len(member_ids) != expected_length:
            return (
                False,
                f"Coordinate must have {expected_length} elements "
                f"(matching dimension count), got {len(member_ids)}",
            )

        # Validate each non-zero member ID exists in corresponding dimension
        for i, member_id in enumerate(member_ids):
            if member_id == 0:  # 0 means "not used" - always valid
                continue

            dimension_position = i + 1
            dimension = self.get_dimension(dimension_position)

            if not dimension:
                return (
                    False,
                    f"No dimension found at position {dimension_position}",
                )

            # Check if member_id exists in this dimension
            if dimension.member:
                member_exists = any(
                    m.memberId == member_id for m in dimension.member
                )
                if not member_exists:
                    dim_name = dimension.dimensionNameEn
                    return (
                        False,
                        f"Member ID {member_id} not found in dimension "
                        f"'{dim_name}' (position {dimension_position})",
                    )

        return True, ""

    @property
    def supports_coordinate_queries(self) -> bool:
        """Check if this cube likely supports coordinate-based API queries.

        Census and other snapshot cubes typically don't support coordinate-based
        queries, while time-series cubes (economic indicators, etc.) do.

        Returns:
            True if the cube likely supports coordinate queries, False otherwise.

        Indicators of snapshot cubes (no coordinate query support):
            - Single series (nbSeriesCube == 1)
            - Same start and end date (snapshot in time)
            - Frequency code 18 (occasional/one-time)

        Indicators of time-series cubes (coordinate queries supported):
            - Multiple series (nbSeriesCube > 1)
            - Date range (cubeStartDate != cubeEndDate)
            - Regular frequency (monthly, quarterly, etc.)

        Example:
            >>> cube = await client.get_cube_metadata(98100001)  # Census
            >>> cube.supports_coordinate_queries
            False
            >>> cube = await client.get_cube_metadata(18100004)  # CPI
            >>> cube.supports_coordinate_queries
            True

        Note:
            This is a heuristic based on observed patterns. There may be
            exceptions. If coordinate queries fail with 406 errors, the cube
            likely doesn't support them regardless of this check.

        """
        # Check if it's a snapshot (single time period)
        is_snapshot = self.cubeStartDate == self.cubeEndDate

        # Check if it's a single series cube
        is_single_series = self.nbSeriesCube is not None and self.nbSeriesCube == 1

        # Frequency code 18 typically means "occasional" or one-time
        occasional_frequency = 18
        is_occasional = self.frequencyCode == occasional_frequency

        # If any snapshot indicator is present, likely no coordinate support
        if is_snapshot or is_single_series or is_occasional:
            return False

        # Otherwise, likely supports coordinate queries
        return True

