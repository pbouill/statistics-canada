from datetime import date, datetime, timezone
from enum import Enum, auto
from typing import Iterator, Optional
import logging

# from httpx import AsyncClient, Response, DEFAULT_TIMEOUT_CONFIG
from httpx._client import AsyncClient, TimeoutTypes, Timeout, DEFAULT_TIMEOUT_CONFIG
# from httpx._types import TimeoutTypes

from statscan.url import WDS_URL

from .requests import WDSRequests
from .coordinate import Coordinate
from .models.cube import Cube, Cube
from .models.datapoint import DataPoint
from .models.vector import Vector
from .models.series import Series


DEFAULT_WDS_TIMEOUT = Timeout(30.0)  # 30 seconds

logger = logging.getLogger(__name__)


class CubeExistsError(ValueError):
    pass


class CubeManager:
    def __init__(self, cubes: Optional[list[Cube]] = None):
        self.__cubes: list[Cube] = cubes or []
        # self.last_update: Optional[datetime] = None

    @property
    def cubes(self) -> dict[int, Cube]:
        return {cube.productId: cube for cube in self.__cubes}

    @property
    def latest_cube(self) -> Optional[Cube]:
        if not self.__cubes:
            return None
        return max(self.__cubes, key=lambda c: c.releaseTime)

    def add_cube(self, cube: Cube, replace: bool = False) -> None:
        if (existing_cube := self.cubes.get(cube.productId)) is not None:
            if not replace:
                raise CubeExistsError(
                    f"Cube with product ID {cube.productId} already exists. Cannot add {cube}"
                )
            else:
                self.remove_cube(existing_cube)
        self.__cubes.append(cube)

    def remove_cube(self, cube: int | Cube) -> None:
        if isinstance(cube, int):
            cube = self[cube]
        self.__cubes.remove(cube)

    def __getitem__(self, product_id: int) -> Cube:
        if (cube := self.cubes.get(product_id)) is None:
            raise KeyError(f"Cube with product ID {product_id} does not exist.")
        return cube

    def __setitem__(self, product_id: int, cube: Cube) -> None:
        if (existing_cube := self.cubes.get(product_id)) is not None:
            self.__cubes.remove(existing_cube)
        self.__cubes.append(cube)

    def __iter__(self):
        return iter(self.__cubes)


class Client(AsyncClient):
    """
    Implemented per the WDS User Guide: https://www.statcan.gc.ca/en/developers/wds/user-guide
    """

    def __init__(
        self, 
        base_url: str = WDS_URL, 
        timeout: TimeoutTypes = DEFAULT_WDS_TIMEOUT, 
        **kwargs):
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
        self.cube_manager: CubeManager = CubeManager()
        super().__init__(base_url=base_url, timeout=timeout, **kwargs)
  
    async def update_cubes(self) -> set[int]:
        cubes = await self.get_all_cubes_list_lite()
        new_cubes: set[int] = set()
        for cube in cubes:
            try:
                self.cube_manager.add_cube(cube)
                new_cubes.add(cube.productId)
            except CubeExistsError:
                logger.debug(f"Cube with product ID {cube.productId} already exists. Replacing.")
                self.cube_manager.add_cube(cube, replace=True)
        return new_cubes

    async def update(self):
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
        coro = WDSRequests.get_changed_cube_list(
            client=self, 
            change_date=change_date
        )
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
        coro = WDSRequests.get_cube_metadata(
            client=self, 
            product_id=product_id
        )
        data = await WDSRequests.execute_and_extract(coro, model=Cube)
        if not isinstance(data, Cube):
            raise TypeError(f"Expected data to be a {Cube}. Got {type(data)}")
        return data

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
            client=self, 
            product_id=product_id, coordinate=str(coordinate)
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
        coro = WDSRequests.get_series_info_from_vector(
            client=self, 
            vector_id=vector_id
        )
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
            client=self, 
            product_id=product_id, coordinate=str(coordinate)
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
            client=self,
            vector_id=vector_id
        )
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, Series):
            raise TypeError(f"Expected data to be a {Series}. Got {type(data)}")
        return data

    async def get_data_from_cube_pid_coord_and_latest_n_periods(
        self, product_id: int, coordinate: str | Coordinate, n: int
    ) -> Series:
        """
        Get data from a cube product ID, coordinate, and the latest N periods.

        Args:
            product_id (int): The product ID of the cube.
            coordinate (str | Coordinate): The coordinate to query.
            n (int): The number of latest periods to retrieve.

        Returns:
            Series: The Series object populated with the returned information.
        """
        coro = WDSRequests.get_data_from_cube_pid_coord_and_latest_n_periods(
            client=self, 
            product_id=product_id, 
            coordinate=str(coordinate), 
            n=n
        )
        data = await WDSRequests.execute_and_extract(coro, model=Series)
        if not isinstance(data, Series):
            raise TypeError(f"Expected data to be a {Series}. Got {type(data)}")
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
            client=self, 
            vector_id=vector_id, 
            n=n
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
            client=self, 
            vector_ids=vector_ids, 
            start=start, 
            end=end
        )
        data = await WDSRequests.execute_and_extract(coro, model=Vector)
        if not isinstance(data, list):
            raise TypeError(f"Expected data to be a {list} of {Vector}. Got {type(data)}")
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
            client=self, 
            vector_ids=vector_ids, 
            start=start, 
            end=end
        )
        data = await WDSRequests.execute_and_extract(coro, model=Vector)
        if not isinstance(data, list):
            raise TypeError(f"Expected data to be a {list} of {Vector}. Got {type(data)}")
        return data

    # TODO: implement get_full_table_download_[csv,sdmx]

    async def get_code_sets(self) -> dict:
        """
        Get the code sets from the WDS API.

        Returns:
            dict: A dictionary of code sets.
        """
        coro = WDSRequests.get_code_sets(client=self)
        data = await WDSRequests.execute_and_extract(coro)
        if not isinstance(data, dict):
            raise TypeError(f"Expected data to be a {dict}. Got {type(data)}")
        return data
