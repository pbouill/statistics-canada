from datetime import date, datetime
from typing import Iterable, Callable, Coroutine, Any, ParamSpec, Concatenate
from enum import Enum, StrEnum, auto
import logging

from httpx import AsyncClient, Response

from statscan.url import WDS_URL

from .coordinate import Coordinate
from .cube import Cube, BaseCube
from .datapoint import DataPoint
from .vector import Vector
from .series import Series


RESPONSE_SUCCESS_STR = 'SUCCESS'

logger = logging.getLogger(__name__)

P = ParamSpec('P')


class ResponseKeys(StrEnum):
    OBJECT = auto()
    STATUS = auto()


class ResponseLanguage(StrEnum):
    EN = auto()
    FR = auto()


class TableFormat(Enum):
    CSV = auto()
    SDMX = auto()


class WDSRequests:
    """
    This class is responsible for minimal http requests to the WDS API.
    Responses typically contain a status (str) and an object (dict).
    """
    METHOD_SIG = Callable[Concatenate[AsyncClient, P], Coroutine[Any, Any, Response]]
    
    @staticmethod
    async def get_changed_series_list(client: AsyncClient) -> Response:
        return await client.get('/getChangedSeriesList')

    @staticmethod
    async def get_changed_cube_list(client: AsyncClient, change_date: datetime | date) -> Response:
        if isinstance(change_date, datetime):
            change_date = change_date.date()
        return await client.get(f'/getChangedCubeList/{change_date.isoformat()}')

    @staticmethod
    async def get_cube_metadata(client: AsyncClient, product_id: int) -> Response:
        return await client.post(f'/getCubeMetadata', json={'productId': product_id})

    @staticmethod
    async def get_series_info_from_cube_pid_coord(client: AsyncClient, product_id: int, coordinate: str) -> Response:  # TODO: perhaps coord should be a class
        return await client.post(f'/getSeriesInfoFromCubePidCoord', json={'productId': product_id, 'coordinate': coordinate})

    @staticmethod
    async def get_series_info_from_vector(client: AsyncClient, vector_id: int) -> Response:
        return await client.post(f'/getSeriesInfoFromVector', json={'vectorId': vector_id})
    
    @staticmethod
    async def get_all_cubes_list(client: AsyncClient) -> Response:
        return await client.get(f'/getAllCubesList')
    
    @staticmethod
    async def get_all_cubes_list_lite(client: AsyncClient) -> Response:
        return await client.get(f'/getAllCubesListLite')

    @staticmethod
    async def get_changed_series_data_from_cube_pid_coord(client: AsyncClient, product_id: int, coordinate: str) -> Response:
        return await client.post(f'/getChangedSeriesDataFromCubePidCoord', json={'productId': product_id, 'coordinate': coordinate})
    
    @staticmethod
    async def get_changed_series_data_from_vector(client: AsyncClient, vector_id: int) -> Response:
        return await client.post(f'/getChangedSeriesDataFromVector', json={'vectorId': vector_id})
    
    @staticmethod
    async def get_data_from_cube_pid_coord_and_latest_n_periods(client: AsyncClient, product_id: int, coordinate: str, n: int) -> Response:
        return await client.post(f'/getDataFromCubePidCoordAndLatestNPeriods', json={'productId': product_id, 'coordinate': coordinate, 'latestN': n})
    
    @staticmethod
    async def get_data_from_vector_and_latest_n_periods(client: AsyncClient, vector_id: int, n: int) -> Response:
        return await client.post(f'/getDataFromVectorsAndLatestNPeriods', json={'vectorId': [vector_id], 'latestN': n})
    
    @staticmethod
    async def get_bulk_vector_data_by_range(client: AsyncClient, vector_ids: list[int], start: datetime, end: datetime) -> Response:
        return await client.post(
            url=f'/getBulkVectorDataByRange', 
            json={
                'vectorIds': vector_ids, 
                'startDataPointReleaseDate': start.isoformat(), 
                'endDataPointReleaseDate': end.isoformat()
            }
        )
    
    @staticmethod
    async def get_data_from_vector_by_reference_period_range(client: AsyncClient, vector_ids: list[int], start: date, end: date) -> Response:
        return await client.get(
            url=f'/getDataFromVectorByReferencePeriodRange',
            params={
                'vectorIds': vector_ids,
                'startRefPeriod': start.isoformat(),
                'endDataPointReleaseDate': end.isoformat()
            }
        )
    
    @staticmethod
    async def get_full_table_download_csv(client: AsyncClient, table_id: int, language: ResponseLanguage) -> Response:
        return await client.get(f'/getFullTableDownloadCSV/{table_id}/{language.value}')
    
    @staticmethod
    async def get_full_table_download_sdmx(client: AsyncClient, table_id: int) -> Response:
        return await client.get(f'/getFullTableDownloadSDMX/{table_id}')
    
    @staticmethod
    async def get_code_sets(client: AsyncClient) -> Response:
        return await client.get(f'/getCodeSets')

    @staticmethod
    def extract_response_object(resp: Response) -> dict:
        """
        Extract the main object from the WDS API response.
        
        Args:
            resp (Response): The HTTP response from the WDS API.
        
        Returns:
            dict: The main object from the response.
        
        Raises:
            KeyError: If the response does not contain the expected object key.
        """
        resp.raise_for_status()
        data = resp.json()
        if ResponseKeys.STATUS in data and data[ResponseKeys.STATUS] != RESPONSE_SUCCESS_STR:
            logger.warning(f'WDS response status not successful: {data[ResponseKeys.STATUS]}')
        return data[ResponseKeys.OBJECT]
    
    @staticmethod
    async def execute_method(method: METHOD_SIG, client: AsyncClient, *args, extract_object: bool = True, **kwargs) -> dict:
        """
        Execute a WDS API method.

        Args:
            method (METHOD_SIG): The method to execute.
            client (AsyncClient): The HTTP client to use.
            *args (Any): The arguments to pass to the method.
            **kwargs (Any): The keyword arguments to pass to the method.

        Returns:
            dict: The main object from the response.
        """
        resp = await method(client, *args, **kwargs)
        if extract_object:
            return WDSRequests.extract_response_object(resp=resp)
        else:
            resp.raise_for_status()
            return resp.json()
        
    @staticmethod
    async def execute_coro(coro: Coroutine[Any, Any, Response], extract_object: bool = True) -> dict:
        """
        Execute a coroutine that returns a WDS API response.

        Args:
            coro (Coroutine[Any, Any, Response]): The coroutine to execute.
            extract_object (bool): Whether to extract the main object from the response.

        Returns:
            dict: The main object from the response.
        """
        resp = await coro
        if extract_object:
            return WDSRequests.extract_response_object(resp=resp)
        else:
            resp.raise_for_status()
            return resp.json()

        


class WDS:
    """
    Implemented per the WDS User Guide: https://www.statcan.gc.ca/en/developers/wds/user-guide
    """

    def __init__(self, base_url: str = WDS_URL):
        """
        Initialize the WDS client with the base URL.
        
        Args:
            base_url (str): The base URL for the WDS API.
        """
        self.client = AsyncClient(base_url=base_url)

    @property
    def base_url(self) -> str:
        """
        Get the base URL for the WDS API.
        
        Returns:
            str: The base URL.
        """
        return str(self.client.base_url)

    async def get_changed_series_list(self) -> list[Series]:
        coro = WDSRequests.get_changed_series_list(client=self.client)
        data = await WDSRequests.execute_coro(coro)
        return [Series.model_validate(item) for item in data]
    
    async def get_changed_cube_list(self, change_date: datetime | date) -> list[Cube]:
        """
        Get a list of changed cubes for a specific date.

        Args:
            change_date (datetime | date): The date to query for changes.
        Returns:
            list[Cube]: A list of changed cubes.
        """
        coro = WDSRequests.get_changed_cube_list(client=self.client, change_date=change_date)
        data = await WDSRequests.execute_coro(coro)
        return [Cube.model_validate(item) for item in data]

    async def get_cube_metadata(self, product_id: int) -> Cube:
        """
        Get metadata for a specific cube product ID.

        Args:
            product_id (int): The product ID of the cube.
        Returns:
            Cube: The Cube object populated with the returned metadata.
        """
        coro = WDSRequests.get_cube_metadata(client=self.client, product_id=product_id)
        data = await WDSRequests.execute_coro(coro)
        return Cube.model_validate(data)

    async def get_series_info_from_cube_pid_coord(self, product_id: int, coordinate: str | Coordinate) -> Series:
        """
        Get series information from a cube product ID.

        Args:
            product_id (int): The product ID of the cube.
        Returns:
            Series: The Series object populated with the returned information.
        """
        coro = WDSRequests.get_series_info_from_cube_pid_coord(client=self.client, product_id=product_id, coordinate=str(coordinate))
        data = await WDSRequests.execute_coro(coro)
        return Series.model_validate(data)
    
    async def get_series_info_from_vector(self, vector_id: int) -> Series:
        """
        Get series information from a vector ID.

        Args:
            vector_id (int): The vector ID to retrieve information for.

        Returns:
            Series: The Series object populated with the returned information.
        """
        coro = WDSRequests.get_series_info_from_vector(client=self.client, vector_id=vector_id)
        data = await WDSRequests.execute_coro(coro)
        return Series.model_validate(data)
    
    async def get_all_cubes_list(self) -> list[Cube]:
        """
        Get a list of all cubes.

        Returns:
            list[Cube]: A list of all Cube objects.
        """
        coro = WDSRequests.get_all_cubes_list(client=self.client)
        data = await WDSRequests.execute_coro(coro)
        return [Cube.model_validate(item) for item in data]
    

    async def get_all_cubes_list_lite(self) -> list[BaseCube]:
        """
        Get a lightweight list of all cubes.

        Returns:
            list[BaseCube]: A list of all BaseCube objects.
        """
        coro = WDSRequests.get_all_cubes_list_lite(client=self.client)
        data = await WDSRequests.execute_coro(coro)
        return [Cube.model_validate(item) for item in data]

    async def get_changed_series_data_from_cube_pid_coord(self, product_id: int, coordinate: str | Coordinate) -> Series:
        """
        Get changed series data from a cube product ID and coordinate.

        Args:
            product_id (int): The product ID of the cube.
            coordinate (str | Coordinate): The coordinate to query.

        Returns:
            Series: The Series object populated with the returned information.
        """
        coro = WDSRequests.get_changed_series_data_from_cube_pid_coord(client=self.client, product_id=product_id, coordinate=str(coordinate))
        data = await WDSRequests.execute_coro(coro)
        return Series.model_validate(data)

    async def get_changed_series_data_from_vector(self, vector_id: int) -> Series:
        """
        Get changed series data from a vector ID.

        Args:
            vector_id (int): The vector ID to query.

        Returns:
            Series: The Series object populated with the returned information.
        """
        coro = WDSRequests.get_changed_series_data_from_vector(client=self.client, vector_id=vector_id)
        data = await WDSRequests.execute_coro(coro)
        return Series.model_validate(data)
    
    async def get_data_from_cube_pid_coord_and_latest_n_periods(self, product_id: int, coordinate: str | Coordinate, n: int) -> Series:
        """
        Get data from a cube product ID, coordinate, and the latest N periods.

        Args:
            product_id (int): The product ID of the cube.
            coordinate (str | Coordinate): The coordinate to query.
            n (int): The number of latest periods to retrieve.

        Returns:
            Series: The Series object populated with the returned information.
        """
        coro = WDSRequests.get_data_from_cube_pid_coord_and_latest_n_periods(client=self.client, product_id=product_id, coordinate=str(coordinate), n=n)
        data = await WDSRequests.execute_coro(coro)
        return Series.model_validate(data)

    async def get_data_from_vector_and_latest_n_periods(self, vector_id: int, n: int) -> Series:
        """
        Get data from a vector ID and the latest N periods.

        Args:
            vector_id (int): The vector ID to query.
            n (int): The number of latest periods to retrieve.

        Returns:
            Series: The Series object populated with the returned information.
        """
        coro = WDSRequests.get_data_from_vector_and_latest_n_periods(client=self.client, vector_id=vector_id, n=n)
        data = await WDSRequests.execute_coro(coro)
        return Series.model_validate(data)
    
    async def get_bulk_vector_data_by_range(self, vector_ids: list[int], start: datetime, end: datetime) -> list[Vector]:
        """
        Get bulk vector data by a range of vector IDs and dates.

        Args:
            vector_ids (list[int]): The list of vector IDs to query.
            start (datetime | date): The start date of the range.
            end (datetime | date): The end date of the range.

        Returns:
            dict: A dictionary mapping vector IDs to their corresponding Series objects.
        """
        coro = WDSRequests.get_bulk_vector_data_by_range(client=self.client, vector_ids=vector_ids, start=start, end=end)
        data = await WDSRequests.execute_coro(coro)
        return [Vector.model_validate(item) for item in data]
    
    async def get_data_from_vector_by_reference_period_range(self, vector_ids: list[int], start: date, end: date) -> list[Vector]:
        """
        Get data from vector IDs by a range of reference periods.

        Args:
            vector_ids (list[int]): The list of vector IDs to query.
            start (date): The start reference period.
            end (date): The end reference period.

        Returns:
            list[Vector]: A list of Vector objects populated with the returned information.
        """
        coro = WDSRequests.get_data_from_vector_by_reference_period_range(client=self.client, vector_ids=vector_ids, start=start, end=end)
        data = await WDSRequests.execute_coro(coro)
        return [Vector.model_validate(item) for item in data]
    
    # TODO: implement get_full_table_download_[csv,sdmx]
    
    async def get_code_sets(self) -> dict:
        """
        Get the code sets from the WDS API.

        Returns:
            dict: A dictionary of code sets.
        """
        coro = WDSRequests.get_code_sets(client=self.client)
        data = await WDSRequests.execute_coro(coro)
        return data
