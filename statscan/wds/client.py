"""Statistics Canada Web Data Service (WDS) API client implementation.

This module provides the main `Client` class for interacting with the WDS API,
supporting all documented endpoints including cube metadata, series data,
vector information, and geographic queries.

Official Documentation: https://www.statcan.gc.ca/en/developers/wds/user-guide
"""
import logging
from datetime import date, datetime
from typing import Any, TypeVar

import numpy as np
import pandas as pd
from httpx._client import AsyncClient, Timeout, TimeoutTypes

from statscan.url import WDS_URL
from statscan.wds.models.code import CodeSets

from ..enums.auto.wds.product_id import ProductID
from ..enums.auto.wds.scalar import Scalar
from ..enums.auto.wds.symbol import Symbol
from .coordinate import Coordinate, create_enhanced_demographic_dataframe
from .cube_manager import CubeManager
from .geographic import GeographicEntity
from .models.cube import Cube, CubeExistsError
from .models.datapoint import DataPoint
from .models.series import ChangedSeriesData, Series
from .models.vector import Vector
from .requests import WDSRequests

# Conservative timeout configuration for reliable operation in all environments
# Note: Connect timeout increased to 120s to handle intermittent TLS handshake
# delays observed with Statistics Canada servers, particularly affecting Python 3.13+
DEFAULT_WDS_TIMEOUT = Timeout(
    connect=120.0,  # Connection timeout - increased for TLS handshake reliability
    read=180.0,  # Read timeout - generous for large responses
    write=60.0,  # Write timeout - increased for reliability
    pool=30.0,  # Pool timeout - increased for connection management
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


class Client(AsyncClient):
    """Statistics Canada Web Data Service (WDS) API Client.

    📚 OFFICIAL DOCUMENTATION: https://www.statcan.gc.ca/en/developers/wds/user-guide

    This client implements all WDS API endpoints as specified in the official
    Statistics Canada WDS User Guide. All method implementations follow the
    exact specifications and parameter requirements documented in the guide.

    For API usage, endpoints, rate limits, and troubleshooting, always refer
    to the official WDS User Guide at the URL above.
    """

    def __init__(
        self,
        base_url: str = WDS_URL,
        timeout: TimeoutTypes = DEFAULT_WDS_TIMEOUT,
        http2: bool = False,  # Disable HTTP/2 for better compatibility
        **kwargs,
    ):
        """Initialize the WDS client (subclass of httpx.AsyncClient).

        Args:
            base_url: The base URL for the WDS API. Defaults to WDS_URL.
            timeout: The timeout configuration to use when sending requests.
                Defaults to 120 seconds for connect, 180s for read.
            http2: Enable HTTP/2 support. Defaults to False for reliability.
            **kwargs: Additional keyword arguments passed to AsyncClient:
                - auth: Authentication class to use when sending requests
                - params: Query parameters to include in request URLs
                - headers: Dictionary of HTTP headers for requests
                - cookies: Dictionary of Cookie items for requests
                - verify: SSL verification (True, False, or ssl.SSLContext)
                - proxy: A proxy URL where all traffic should be routed
                - limits: The limits configuration to use
                - max_redirects: Maximum number of redirect responses
                - transport: A transport class for sending requests
                - trust_env: Enables/disables environment variables usage
                - default_encoding: Default encoding for decoding responses

        """
        self.codesets: CodeSets | None = None
        self.cube_manager: CubeManager = CubeManager()
        super().__init__(base_url=base_url, timeout=timeout, http2=http2, **kwargs)

    async def update_codesets(self) -> set[str]:
        """Update the internal codesets with the latest from the WDS API.

        Returns:
            set[str]: A set of code set names that were updated.

        """
        self.codesets = await self.get_code_sets()
        return set(self.codesets.keys())

    async def update_cubes(self) -> set[int]:
        """Update the internal cube manager with the latest cubes from the WDS API.

        Returns:
            set[int]: A set of product IDs for the newly added cubes.

        """
        cubes = await self.get_all_cubes_list_lite()
        new_cubes: set[int] = set()
        for cube in cubes:
            try:
                self.cube_manager.add_cube(cube)
                new_cubes.add(cube.productId)
            except CubeExistsError:
                logger.debug(
                    f"Cube with product ID {cube.productId} already exists. Replacing."
                )
                self.cube_manager.add_cube(cube, replace=True)
        return new_cubes

    async def update_cube(self, product_id: int) -> Cube:
        """Update or add a specific cube by its product ID.

        Args:
            product_id (int): The product ID of the cube to update or add.

        """
        cube = await self.get_cube_metadata(product_id=product_id)
        self.cube_manager.add_cube(cube, replace=True)
        return cube

    async def update(self, codesets: bool = True, cubes: bool = True) -> None:
        """Update internal codesets and cubes from the WDS API.

        Args:
            codesets: Whether to update codesets.
            cubes: Whether to update cubes.

        """
        await self.update_codesets()
        await self.update_cubes()

    @property
    def cubes(self) -> dict[int, Cube]:
        """Get the dictionary of cubes indexed by product ID."""
        return self.cube_manager.cubes

    async def get_changed_series_list(self) -> list[Series]:
        """Get the list of series that have changed.

        Returns:
            A list of Series objects representing changed series.

        """
        coro = WDSRequests.get_changed_series_list(client=self)
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, list):
            raise TypeError(f"Expected data to be a list of {Series}. Got {type(data)}")
        return data

    async def get_changed_cube_list(self, change_date: datetime | date) -> list[Cube]:
        """Get a list of changed cubes for a specific date.

        Args:
            change_date (datetime | date): The date to query for changes.

        Returns:
            list[Cube]: A list of changed cubes.

        """
        coro = WDSRequests.get_changed_cube_list(client=self, change_date=change_date)
        data = await WDSRequests.execute_and_extract(coro, model=Cube)
        if not isinstance(data, list):
            raise TypeError(f"Expected data to be a {list} of {Cube}. Got {type(data)}")
        return data

    async def get_cube_metadata(self, product_id: int) -> Cube:
        """Get metadata for a specific cube product ID.

        Args:
            product_id: The product ID of the cube.

        Returns:
            The Cube object populated with the returned metadata.

        """
        coro = WDSRequests.get_cube_metadata(client=self, product_id=product_id)
        data = await WDSRequests.execute_and_extract(coro, model=Cube)
        if isinstance(data, list) and len(data) == 1:
            return data[0]
        elif isinstance(data, Cube):
            return data
        else:
            raise TypeError(
                f"Expected data to be a {Cube} or list[{Cube}] with one "
                f"item. Got {type(data)}"
            )

    async def get_series_info_from_cube_pid_coord(
        self, product_id: int, coordinate: str | Coordinate
    ) -> Series:
        """Get series information from a cube product ID and coordinate.

        Args:
            product_id: The product ID of the cube.
            coordinate: The coordinate string or Coordinate object.

        Returns:
            The Series object populated with the returned information.

        """
        coro = WDSRequests.get_series_info_from_cube_pid_coord(
            client=self, product_id=product_id, coordinate=str(coordinate)
        )
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, Series):
            raise TypeError(f"Expected data to be a Series. Got {type(data)}")
        return data

    async def get_series_info_from_vector(self, vector_id: int) -> Series:
        """Get series information from a vector ID.

        Args:
            vector_id (int): The vector ID to retrieve information for.

        Returns:
            Series: The Series object populated with the returned information.

        """
        coro = WDSRequests.get_series_info_from_vector(client=self, vector_id=vector_id)
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, Series):
            raise TypeError(f"Expected data to be a Series. Got {type(data)}")
        return data

    async def get_all_cubes_list(self) -> list[Cube]:
        """Get a list of all cubes.

        Returns:
            list[Cube]: A list of all Cube objects.

        """
        coro = WDSRequests.get_all_cubes_list(client=self)
        data = await WDSRequests.execute_and_extract(coro, model=Cube)
        if not isinstance(data, list):
            raise TypeError(f"Expected data to be a {list} of {Cube}. Got {type(data)}")
        return data

    async def get_all_cubes_list_lite(self) -> list[Cube]:
        """Get a lightweight list of all cubes.

        Returns:
            list[BaseCube]: A list of all BaseCube objects.

        """
        coro = WDSRequests.get_all_cubes_list_lite(client=self)
        data = await WDSRequests.execute_and_extract(coro, model=Cube)
        if not isinstance(data, list):
            raise TypeError(f"Expected data to be a {list} of {Cube}. Got {type(data)}")
        return data

    async def get_changed_series_data_from_cube_pid_coord(
        self, product_id: int, coordinate: str | Coordinate
    ) -> Series:
        """Get changed series data from a cube product ID and coordinate.

        Args:
            product_id (int): The product ID of the cube.
            coordinate (str | Coordinate): The coordinate to query.

        Returns:
            Series: The Series object populated with the returned information.

        """
        coro = WDSRequests.get_changed_series_data_from_cube_pid_coord(
            client=self, product_id=product_id, coordinate=str(coordinate)
        )
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, Series):
            raise TypeError(f"Expected data to be a {Series}. Got {type(data)}")
        return data

    async def get_changed_series_data_from_vector(self, vector_id: int) -> Series:
        """Get changed series data from a vector ID.

        Args:
            vector_id (int): The vector ID to query.

        Returns:
            Series: The Series object populated with the returned information.

        """
        coro = WDSRequests.get_changed_series_data_from_vector(
            client=self, vector_id=vector_id
        )
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, Series):
            raise TypeError(f"Expected data to be a {Series}. Got {type(data)}")
        return data

    async def get_data_from_cube_pid_coord_and_latest_n_periods(
        self, product_id: int, coordinate: str | Coordinate, n: int
    ) -> ChangedSeriesData:
        """Get data from a cube product ID, coordinate, and latest N periods.

        Args:
            product_id: The product ID of the cube.
            coordinate: The coordinate to query.
            n: The number of latest periods to retrieve.

        Returns:
            The ChangedSeriesData object populated with the returned info.

        """
        coro = WDSRequests.get_data_from_cube_pid_coord_and_latest_n_periods(
            client=self, product_id=product_id, coordinate=str(coordinate), n=n
        )
        data = await WDSRequests.execute_and_extract(coro, model=ChangedSeriesData)

        # Handle list response (API returns list with one item)
        if isinstance(data, list):
            if len(data) != 1:
                raise ValueError(
                    f"Expected exactly one ChangedSeriesData object, got {len(data)}"
                )
            data = data[0]

        if not isinstance(data, ChangedSeriesData):
            raise TypeError(
                f"Expected data to be a {ChangedSeriesData}. Got {type(data)}"
            )
        return data

    async def get_data_from_vector_and_latest_n_periods(
        self, vector_id: int, n: int
    ) -> Series:
        """Get data from a vector ID and the latest N periods.

        Args:
            vector_id (int): The vector ID to query.
            n (int): The number of latest periods to retrieve.

        Returns:
            Series: The Series object populated with the returned information.

        """
        coro = WDSRequests.get_data_from_vector_and_latest_n_periods(
            client=self, vector_id=vector_id, n=n
        )
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, Series):
            raise TypeError(f"Expected data to be a {Series}. Got {type(data)}")
        return data

    async def get_bulk_vector_data_by_range(
        self, vector_ids: list[int], start: datetime, end: datetime
    ) -> list[Vector]:
        """Get bulk vector data by a range of vector IDs and dates.

        Args:
            vector_ids (list[int]): The list of vector IDs to query.
            start (datetime | date): The start date of the range.
            end (datetime | date): The end date of the range.

        Returns:
            dict: A dictionary mapping vector IDs to their corresponding Series objects.

        """
        coro = WDSRequests.get_bulk_vector_data_by_range(
            client=self, vector_ids=vector_ids, start=start, end=end
        )
        data = await WDSRequests.execute_and_extract(coro, model=Vector)
        if not isinstance(data, list):
            raise TypeError(
                f"Expected data to be a {list} of {Vector}. Got {type(data)}"
            )
        return data

    async def get_data_from_vector_by_reference_period_range(
        self, vector_ids: list[int], start: date, end: date
    ) -> list[Vector]:
        """Get data from vector IDs by a range of reference periods.

        Args:
            vector_ids: The list of vector IDs to query.
            start: The start reference period.
            end: The end reference period.

        Returns:
            A list of Vector objects populated with the returned info.

        """
        coro = WDSRequests.get_data_from_vector_by_reference_period_range(
            client=self, vector_ids=vector_ids, start=start, end=end
        )
        data = await WDSRequests.execute_and_extract(coro, model=Vector)
        if not isinstance(data, list):
            raise TypeError(
                f"Expected data to be a {list} of {Vector}. Got {type(data)}"
            )
        return data

    # TODO: implement get_full_table_download_[csv,sdmx]
    async def get_code_sets(self) -> CodeSets:
        """Get the code sets from the WDS API.

        Returns:
            CodeSets: A model representing the code sets.

        """
        coro = WDSRequests.get_code_sets(client=self)
        data = await WDSRequests.execute_and_extract(coro, model=CodeSets)
        if not isinstance(data, CodeSets):
            raise TypeError(f"Expected data to be a {CodeSets}. Got {type(data)}")
        return data

    # =======================
    # Geographic & Population Methods
    # =======================

    async def get_population(
        self,
        identifier: str | int,
        product_id: ProductID
        | int = ProductID.POP_AND_DWEL_COUNTS_CAN_AND_CEN_SUBDIVISIONS,
    ) -> int | None:
        """Get population for a location by name or member ID.

        Args:
            identifier: Location name (str) or member ID (int)
            product_id: Product ID for population data (default: ProductID for
                census subdivision population and dwelling counts)

        Returns:
            Population count or None if not found

        Example:
            client = Client()
            population = await client.get_population("Saugeen Shores")
            population = await client.get_population(2314)  # by member ID

        """
        # Convert enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        if isinstance(identifier, int):
            # Direct member ID lookup
            entity = await self.create_entity_from_member_id(identifier)
            return entity.population if entity else None
        else:
            # Name-based lookup requires cube metadata for search
            try:
                cube = await self.get_cube_metadata(pid)
                if not cube.dimensions:
                    return None

                # Find geographic dimension and search members
                geo_dim = None
                for dim in cube.dimensions:
                    if (
                        "geography" in dim.dimensionNameEn.lower()
                        or "geographic" in dim.dimensionNameEn.lower()
                    ):
                        geo_dim = dim
                        break

                if not geo_dim or not geo_dim.member:
                    return None

                # Search for matching member
                search_lower = identifier.lower()
                for member in geo_dim.member:
                    if search_lower in member.memberNameEn.lower():
                        entity = await self.create_entity_from_member_id(
                            member.memberId
                        )
                        return entity.population if entity else None

            except Exception as e:
                logger.debug(
                    f"Failed to get population for {identifier}: {e}"
                )

        return None

    async def get_location_data(  # noqa: PLR0911, PLR0912
        self,
        identifier: str | int,
        format: str = "population",
        periods: int = 1,
        product_id: ProductID
        | int = ProductID.POP_AND_DWEL_COUNTS_CAN_AND_CEN_SUBDIVISIONS,
    ) -> Any:
        """Get location data in various formats.

        Args:
            identifier: Location name or member ID
            format: 'population', 'array', 'dataframe', or 'entity'
            periods: Number of time periods to retrieve
            product_id: Product ID to query (default: ProductID for census subdivision
                population and dwelling counts)

        Returns:
            Data in the requested format

        Example:
            client = Client()
            pop = await client.get_location_data("Saugeen Shores", "population")
            df = await client.get_location_data(2314, "dataframe", periods=5)

        """
        # Convert enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        # Get the geographic entity
        if isinstance(identifier, int):
            entity = await self.create_entity_from_member_id(identifier)
        else:
            # Name-based lookup
            pop = await self.get_population(identifier, pid)
            if pop is None:
                return None
            # Find the member ID from population lookup (this is inefficient, but works)
            # Better implementation would cache the member lookup
            try:
                cube = await self.get_cube_metadata(pid)
                if cube.dimensions:
                    geo_dim = next(
                        (
                            d
                            for d in cube.dimensions
                            if "geography" in d.dimensionNameEn.lower()
                        ),
                        None,
                    )
                    if geo_dim and geo_dim.member:
                        search_lower = identifier.lower()
                        for member in geo_dim.member:
                            if search_lower in member.memberNameEn.lower():
                                entity = await self.create_entity_from_member_id(
                                    member.memberId
                                )
                                break
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            except Exception:
                return None

        if not entity:
            return None

        if format == "population":
            return entity.population
        elif format == "array":
            return await self.get_entity_data_as_array(entity, periods)
        elif format == "dataframe":
            return await self.get_entity_data_as_dataframe(entity, periods)
        elif format == "entity":
            return entity
        else:
            raise ValueError(f"Unknown format: {format}")

    async def search_locations(
        self,
        query: str,
        product_id: ProductID
        | int = ProductID.POP_AND_DWEL_COUNTS_CAN_AND_CEN_SUBDIVISIONS,
    ) -> list[tuple[int, str]]:
        """Search for locations by partial name match.

        Args:
            query: Search query string
            product_id: Product ID to search in (default: ProductID for census
                subdivision population and dwelling counts)

        Returns:
            List of (member_id, name) tuples

        Example:
            client = Client()
            results = await client.search_locations("saugeen")
            # Returns: [(2314, "Saugeen Shores")]

        """
        # Convert enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        try:
            cube = await self.get_cube_metadata(pid)
            if not cube.dimensions:
                return []

            # Find geographic dimension
            geo_dim = next(
                (
                    d
                    for d in cube.dimensions
                    if "geography" in d.dimensionNameEn.lower()
                ),
                None,
            )
            if not geo_dim or not geo_dim.member:
                return []

            # Search members
            query_lower = query.lower()
            matches = []
            for member in geo_dim.member:
                if query_lower in member.memberNameEn.lower():
                    matches.append((member.memberId, member.memberNameEn))

            return matches[:10]  # Limit results

        except Exception:
            return []

    async def create_entity_from_member_id(
        self, member_id: int
    ) -> GeographicEntity:
        """Create a GeographicEntity by discovering its properties from the WDS API.

        Args:
            member_id: The WDS member ID for the geographic entity

        Returns:
            GeographicEntity with populated metadata

        Example:
            client = Client()
            entity = await client.create_entity_from_member_id(2314)
            print(entity.population)

        """
        # Get population data to validate the member ID
        coordinate = f"{member_id}.1.0.0.0.0.0.0.0.0"

        # Try multiple product IDs to find one that works
        product_ids = [98100001, 98100002, 98100004]

        for product_id in product_ids:
            try:
                result = await self.get_data_from_cube_pid_coord_and_latest_n_periods(
                    product_id=product_id, coordinate=coordinate, n=1
                )

                data = (
                    result.vectorDataPoint if hasattr(result, "vectorDataPoint") else []
                )
                if data and len(data) > 0:
                    population = data[0].value if data[0].value is not None else 0
                    return GeographicEntity(
                        member_id=member_id,
                        population=int(population),
                        coordinate=coordinate,
                    )

            except Exception as e:
                logger.debug(
                    "Failed to get data for member %s from product %s: %s",
                    member_id,
                    product_id,
                    e,
                )
                continue  # Try next product ID

        # Return basic entity even if we can't get population
        return GeographicEntity(member_id=member_id)

    async def get_entity_population_data(
        self, entity: GeographicEntity, periods: int = 1
    ) -> list[DataPoint]:
        """Get population data for a geographic entity.

        Args:
            entity: The GeographicEntity to get data for
            periods: Number of time periods to retrieve

        Returns:
            List of DataPoint objects with population data

        Example:
            client = Client()
            entity = await client.create_entity_from_member_id(2314)
            data = await client.get_entity_population_data(entity, periods=5)

        """
        # Try multiple product IDs in order of preference
        product_ids = [
            98100001,  # Population estimates (works for higher-level geographies)
            98100002,  # Census population (works for more geographies)
            98100004,  # Census households (backup for some areas)
        ]

        for product_id in product_ids:
            try:
                result = await self.get_data_from_cube_pid_coord_and_latest_n_periods(
                    product_id=product_id, coordinate=entity.coordinate or "", n=periods
                )

                # Check if we got valid data
                if (
                    hasattr(result, "vectorDataPoint")
                    and result.vectorDataPoint
                    and len(result.vectorDataPoint) > 0
                ):
                    return result.vectorDataPoint

            except Exception as e:
                logger.debug(
                    "Failed to get population data from product %s: %s", product_id, e
                )
                continue  # Try next product ID

        return []  # No data found in any product ID

    async def get_entity_data_as_array(
        self, entity: GeographicEntity, periods: int = 10
    ) -> np.ndarray:
        """Get population data for an entity as a numpy array.

        Args:
            entity: The GeographicEntity to get data for
            periods: Number of time periods to retrieve

        Returns:
            numpy array of population values

        Example:
            client = Client()
            entity = await client.create_entity_from_member_id(2314)
            arr = await client.get_entity_data_as_array(entity, periods=10)

        """
        data = await self.get_entity_population_data(entity, periods)
        values = [float(dp.value) if dp.value is not None else 0.0 for dp in data]
        return np.array(values)

    async def get_entity_data_as_dataframe(
        self,
        entity: GeographicEntity,
        periods: int = 10,
        include_quality_info: bool = True,
    ) -> pd.DataFrame:
        """Get population data for an entity as a pandas DataFrame.

        Args:
            entity: The GeographicEntity to get data for
            periods: Number of time periods to retrieve
            include_quality_info: Whether to include human-readable quality info

        Returns:
            pandas DataFrame with enriched enum information

        Example:
            client = Client()
            entity = await client.create_entity_from_member_id(2314)
            df = await client.get_entity_data_as_dataframe(entity, periods=5)

        """
        data = await self.get_entity_population_data(entity, periods)

        records = []
        for dp in data:
            # Convert enum codes to meaningful descriptions
            status_desc = None
            if dp.statusCode:
                if hasattr(dp.statusCode, "name"):
                    status_desc = dp.statusCode.name.replace("_", " ").title()
                else:
                    status_desc = f"Status {dp.statusCode}"

            symbol_desc = None
            if dp.symbolCode and dp.symbolCode != Symbol.NONE:
                if hasattr(dp.symbolCode, "name"):
                    symbol_desc = dp.symbolCode.name.replace("_", " ").title()
                else:
                    symbol_desc = f"Symbol {dp.symbolCode}"

            scalar_desc = None
            if dp.scalarFactorCode and dp.scalarFactorCode != Scalar.UNITS:
                if hasattr(dp.scalarFactorCode, "name"):
                    scalar_desc = dp.scalarFactorCode.name.replace("_", " ").title()
                else:
                    scalar_desc = f"Scalar {dp.scalarFactorCode}"

            record = {
                "ref_date": dp.refPer,
                "value": float(dp.value) if dp.value is not None else None,
                "status_code": dp.statusCode.value
                if hasattr(dp.statusCode, "value")
                else dp.statusCode,
                "status": status_desc,
                "symbol_code": dp.symbolCode.value
                if hasattr(dp.symbolCode, "value")
                else dp.symbolCode,
                "symbol": symbol_desc,
                "scalar_code": dp.scalarFactorCode.value
                if hasattr(dp.scalarFactorCode, "value")
                else dp.scalarFactorCode,
                "scalar": scalar_desc,
                "member_id": entity.member_id,
                "location": entity.name,
                "coordinate": entity.coordinate,
                "release_time": dp.releaseTime,
                "frequency": dp.frequencyCode.name
                if hasattr(dp.frequencyCode, "name")
                else dp.frequencyCode,
            }

            # Add human-readable quality information if requested
            if include_quality_info:
                record["quality_info"] = GeographicEntity.get_data_quality_info(dp)

            records.append(record)

        return pd.DataFrame(records)

    async def get_entity_demographic_dataframe(
        self,
        entity: GeographicEntity,
        demographic_type: str = "age_gender",
        census_year: int = 2021,
    ) -> pd.DataFrame:
        """Get demographic breakdown data for an entity as a DataFrame.

        Args:
            entity: The GeographicEntity to get data for
            demographic_type: Type of demographic data:
                - "age_gender": Age and gender breakdowns (product 98100020)
                - "age_broad": Broad age groups by gender (product 98100030)
            census_year: Census year (2016 or 2021)

        Returns:
            pandas DataFrame with demographic data

        Example:
            client = Client()
            entity = await client.create_entity_from_member_id(2314)
            df = await client.get_entity_demographic_dataframe(entity, "age_gender")

        """
        # Map demographic types to WDS product IDs
        product_map = {
            "age_gender": 98100020,  # Age (single years), average/median age by gender
            "age_broad": 98100030,  # Broad age groups by gender
        }

        if demographic_type not in product_map:
            available = list(product_map.keys())
            raise ValueError(
                f"Unknown demographic_type: {demographic_type}. "
                f"Available: {available}"
            )

        product_id = product_map[demographic_type]

        # Use enhanced DataFrame creation
        return await create_enhanced_demographic_dataframe(
            entity_member_id=entity.member_id,
            entity_name=entity.name or f"Member {entity.member_id}",
            product_id=product_id,
            demographic_type=demographic_type,
            client=self,
            census_year=census_year,
            max_characteristics=20,  # Limit for performance
        )
