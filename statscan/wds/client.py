from datetime import date, datetime
import logging
from typing import Any, TypeVar

from httpx._client import AsyncClient, TimeoutTypes, Timeout

from statscan.url import WDS_URL
from statscan.wds.models.code import CodeSets

from .requests import WDSRequests
from .cube_manager import CubeManager
from .coordinate import Coordinate
from .models.cube import Cube, CubeExistsError
from .models.vector import Vector
from .models.series import Series, ChangedSeriesData


# Conservative timeout configuration for reliable operation in all environments
DEFAULT_WDS_TIMEOUT = Timeout(
    connect=30.0,  # Connection timeout - increased for reliability
    read=90.0,  # Read timeout - generous for large responses
    write=30.0,  # Write timeout - increased for reliability
    pool=15.0,  # Pool timeout - increased for connection management
)

T = TypeVar("T")

logger = logging.getLogger(__name__)


class Client(AsyncClient):
    """
    Statistics Canada Web Data Service (WDS) API Client.

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
        **kwargs,
    ):
        """
        Initialize the WDS client (subclass of httpx.AsyncClient).

        Args:
            base_url (str): The base URL for the WDS API. Defaults to WDS_URL.
            timeout (TimeoutTypes): The timeout configuration to use when sending requests. Defaults to 30 seconds.
            **kwargs: Additional keyword arguments passed to AsyncClient:
            - auth: Authentication class to use when sending requests
            - params: Query parameters to include in request URLs
            - headers: Dictionary of HTTP headers to include when sending requests
            - cookies: Dictionary of Cookie items to include when sending requests
            - verify: SSL verification setting (True, False, or ssl.SSLContext)
            - http2: Boolean indicating if HTTP/2 support should be enabled
            - proxy: A proxy URL where all traffic should be routed
            - limits: The limits configuration to use
            - max_redirects: The maximum number of redirect responses to follow
            - transport: A transport class to use for sending requests
            - trust_env: Enables or disables usage of environment variables
            - default_encoding: The default encoding for decoding response text
        """
        self.codesets: CodeSets | None = None
        self.cube_manager: CubeManager = CubeManager()
        super().__init__(base_url=base_url, timeout=timeout, **kwargs)

    async def update_codesets(self) -> set[str]:
        """
        Update the internal codesets with the latest from the WDS API.
        Returns:
            set[str]: A set of code set names that were updated."""
        self.codesets = await self.get_code_sets()
        return set(self.codesets.keys())

    async def update_cubes(self) -> set[int]:
        """
        Update the internal cube manager with the latest cubes from the WDS API.
        Returns:
            set[int]: A set of product IDs for the newly added cubes."""
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
        """
        Update or add a specific cube by its product ID.

        Args:
            product_id (int): The product ID of the cube to update or add.
        """
        cube = await self.get_cube_metadata(product_id=product_id)
        self.cube_manager.add_cube(cube, replace=True)
        return cube

    async def update(self, codesets: bool = True, cubes: bool = True) -> None:
        await self.update_codesets()
        await self.update_cubes()

    @property
    def cubes(self) -> dict[int, Cube]:
        return self.cube_manager.cubes

    async def get_changed_series_list(self) -> list[Series]:
        coro = WDSRequests.get_changed_series_list(client=self)
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, list):
            raise TypeError(f"Expected data to be a list of {Series}. Got {type(data)}")
        return data

    async def get_changed_cube_list(self, change_date: datetime | date) -> list[Cube]:
        """
        Get a list of changed cubes for a specific date.

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
        """
        Get metadata for a specific cube product ID.

        Args:
            product_id (int): The product ID of the cube.
        Returns:
            Cube: The Cube object populated with the returned metadata.
        """
        coro = WDSRequests.get_cube_metadata(client=self, product_id=product_id)
        data = await WDSRequests.execute_and_extract(coro, model=Cube)
        if isinstance(data, list) and len(data) == 1:
            return data[0]
        elif isinstance(data, Cube):
            return data
        else:
            raise TypeError(
                f"Expected data to be a {Cube} or list[{Cube}] with one item. Got {type(data)}"
            )

    async def get_series_info_from_cube_pid_coord(
        self, product_id: int, coordinate: str | Coordinate
    ) -> Series:
        """
        Get series information from a cube product ID.

        Args:
            product_id (int): The product ID of the cube.
        Returns:
            Series: The Series object populated with the returned information.
        """
        coro = WDSRequests.get_series_info_from_cube_pid_coord(
            client=self, product_id=product_id, coordinate=str(coordinate)
        )
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, Series):
            raise TypeError(f"Expected data to be a Series. Got {type(data)}")
        return data

    async def get_series_info_from_vector(self, vector_id: int) -> Series:
        """
        Get series information from a vector ID.

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
        """
        Get a list of all cubes.

        Returns:
            list[Cube]: A list of all Cube objects.
        """
        coro = WDSRequests.get_all_cubes_list(client=self)
        data = await WDSRequests.execute_and_extract(coro, model=Cube)
        if not isinstance(data, list):
            raise TypeError(f"Expected data to be a {list} of {Cube}. Got {type(data)}")
        return data

    async def get_all_cubes_list_lite(self) -> list[Cube]:
        """
        Get a lightweight list of all cubes.

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
        """
        Get changed series data from a cube product ID and coordinate.

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
        """
        Get changed series data from a vector ID.

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
        """
        Get data from a cube product ID, coordinate, and the latest N periods.

        Args:
            product_id (int): The product ID of the cube.
            coordinate (str | Coordinate): The coordinate to query.
            n (int): The number of latest periods to retrieve.

        Returns:
            ChangedSeriesData: The ChangedSeriesData object populated with the returned information.
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
        """
        Get data from a vector ID and the latest N periods.

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
        """
        Get bulk vector data by a range of vector IDs and dates.

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
        """
        Get data from vector IDs by a range of reference periods.

        Args:
            vector_ids (list[int]): The list of vector IDs to query.
            start (date): The start reference period.
            end (date): The end reference period.

        Returns:
            list[Vector]: A list of Vector objects populated with the returned information.
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
        """
        Get the code sets from the WDS API.

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
        self, identifier: str | int, product_id: int = 98100002
    ) -> int | None:
        """
        Get population for a location by name or member ID.

        Args:
            identifier: Location name (str) or member ID (int)
            product_id: Product ID for population data (default: 98100002)

        Returns:
            Population count or None if not found

        Example:
            client = Client()
            population = await client.get_population("Saugeen Shores")
            population = await client.get_population(2314)  # by member ID
        """
        from .geographic import GeographicEntity

        if isinstance(identifier, int):
            # Direct member ID lookup
            entity = await GeographicEntity.from_member_id(identifier, self)
            return entity.population if entity else None
        else:
            # Name-based lookup requires cube metadata for search
            try:
                cube = await self.get_cube_metadata(product_id)
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
                        entity = await GeographicEntity.from_member_id(
                            member.memberId, self
                        )
                        return entity.population if entity else None

            except Exception:
                pass

        return None

    async def get_location_data(
        self,
        identifier: str | int,
        format: str = "population",
        periods: int = 1,
        product_id: int = 98100002,
    ) -> Any:
        """
        Get location data in various formats.

        Args:
            identifier: Location name or member ID
            format: 'population', 'array', 'dataframe', or 'entity'
            periods: Number of time periods to retrieve
            product_id: Product ID to query

        Returns:
            Data in the requested format

        Example:
            client = Client()
            pop = await client.get_location_data("Saugeen Shores", "population")
            df = await client.get_location_data(2314, "dataframe", periods=5)
        """
        from .geographic import GeographicEntity

        # Get the geographic entity
        if isinstance(identifier, int):
            entity = await GeographicEntity.from_member_id(identifier, self)
        else:
            # Name-based lookup
            pop = await self.get_population(identifier, product_id)
            if pop is None:
                return None
            # Find the member ID from population lookup (this is inefficient, but works)
            # Better implementation would cache the member lookup
            try:
                cube = await self.get_cube_metadata(product_id)
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
                                entity = await GeographicEntity.from_member_id(
                                    member.memberId, self
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
            return await entity.get_data_as_array(self, periods)
        elif format == "dataframe":
            return await entity.get_data_as_dataframe(self, periods)
        elif format == "entity":
            return entity
        else:
            raise ValueError(f"Unknown format: {format}")

    async def search_locations(
        self, query: str, product_id: int = 98100002
    ) -> list[tuple[int, str]]:
        """
        Search for locations by partial name match.

        Args:
            query: Search query string
            product_id: Product ID to search in (default: 98100002)

        Returns:
            List of (member_id, name) tuples

        Example:
            client = Client()
            results = await client.search_locations("saugeen")
            # Returns: [(2314, "Saugeen Shores")]
        """
        try:
            cube = await self.get_cube_metadata(product_id)
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
