from datetime import date, datetime
import logging
from enum import StrEnum, auto
from typing import (
    Any,
    Callable,
    Concatenate,
    Coroutine,
    Optional,
    ParamSpec,
    TypeVar,
    overload,
)

from httpx._client import AsyncClient, Response
from pydantic import BaseModel


P = ParamSpec("P")
_T = TypeVar("_T", bound=BaseModel)

RESPONSE_SUCCESS_STR = "SUCCESS"

logger = logging.getLogger(__name__)


class ResponseLanguage(StrEnum):
    EN = auto()
    FR = auto()


class ResponseKeys(StrEnum):
    OBJECT = "object"
    STATUS = "status"


class WDSRequests:
    """
    Low-level HTTP requests for Statistics Canada WDS API.

    📚 OFFICIAL WDS DOCUMENTATION: https://www.statcan.gc.ca/en/developers/wds/user-guide

    This class implements the exact HTTP request patterns specified in the
    Statistics Canada WDS User Guide. All endpoint URLs, request methods,
    and parameter formats follow the official API specification.

    Response Format: {"status": "SUCCESS|FAILED", "object": {...}}
    """

    METHOD_SIG = Callable[Concatenate[AsyncClient, P], Coroutine[Any, Any, Response]]

    @overload
    @staticmethod
    async def execute_and_extract(
        coro: Coroutine[Any, Any, Response], model: type[_T]
    ) -> _T | list[_T]: ...

    @overload
    @staticmethod
    async def execute_and_extract(
        coro: Coroutine[Any, Any, Response], model: None = None
    ) -> dict | list[dict]: ...

    @staticmethod
    async def execute_and_extract(
        coro: Coroutine[Any, Any, Response],
        model: Optional[type[_T]] = None,
    ) -> _T | list[_T] | dict | list[dict]:
        """
        Execute a coroutine that returns a WDS API response.

        Args:
            coro (Coroutine[Any, Any, Response]): The coroutine to execute.
            model (Optional[type[WDSBaseModel]]): The model to parse the response object into.

        Returns:
            dict: The main object from the response.
        """
        resp = await coro
        resp.raise_for_status()

        data = resp.json()
        logger.debug(f"Response code: {resp.status_code}, Response JSON: {data}")

        if model:
            if isinstance(data, list):
                # Check if this is wrapped format [{"status": "SUCCESS", "object": {...}}] or direct format [{...}]
                if len(data) > 0 and ResponseKeys.OBJECT in data[0]:
                    # Wrapped format: extract object field
                    return [
                        WDSRequests.dict_to_model(item[ResponseKeys.OBJECT], model)
                        for item in data
                    ]
                else:
                    # Direct format: use items directly
                    return [WDSRequests.dict_to_model(item, model) for item in data]
            elif isinstance(data, dict):
                obj = data[ResponseKeys.OBJECT]
                return WDSRequests.dict_to_model(obj, model)
            else:
                raise TypeError(
                    f"Response JSON is neither a dict nor a list of dicts: {type(data)}"
                )
        elif isinstance(data, (list, dict)):
            if isinstance(data, list):
                # Check if this is wrapped format [{"status": "SUCCESS", "object": {...}}] or direct format [{...}]
                if len(data) > 0 and ResponseKeys.OBJECT in data[0]:
                    # Wrapped format: extract object field
                    return [item[ResponseKeys.OBJECT] for item in data]
                else:
                    # Direct format: return as-is
                    return data
            elif isinstance(data, dict):
                if ResponseKeys.OBJECT in data:
                    return data[ResponseKeys.OBJECT]
            return data
        else:
            raise TypeError(
                f"Response JSON is neither a dict nor a list of dicts: {type(data)}"
            )

    @staticmethod
    def dict_to_model(data: dict, model: type[_T]) -> _T:
        """
        Convert a dictionary to a Pydantic model.

        Args:
            data (dict): The dictionary to convert.
            model (type[WDSBaseModel]): The model to convert the dictionary to.

        Returns:
            WDSBaseModel: The converted model.
        """
        try:
            return model.model_validate(obj=data)
        except Exception as e:
            data_str = "\n".join([f"{k}:{v}" for k, v in data.items()])
            logger.error(f"Error converting dict to {model}: {e}.\nData:\n{data_str}")
            raise e

    @staticmethod
    async def get_changed_series_list(client: AsyncClient) -> Response:
        """
        Users can choose to ask for what series have changed today. This can be invoked
        at any time of day and will reflect the list of series that have been updated at
        8:30am EST on a given release up until midnight that same day.

        Args:
            client (AsyncClient): The HTTP client to use for the request.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.get("/getChangedSeriesList")

    @staticmethod
    async def get_changed_cube_list(
        client: AsyncClient, change_date: datetime | date
    ) -> Response:
        """
        Users can also query what has changed at the table/cube level on a specific day
        by adding an ISO date to the end of the URL. This date can be any date from
        today into the past.

        Args:
            client (AsyncClient): The HTTP client to use for the request.
            change_date (datetime | date): The date to query for changes.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        if isinstance(change_date, datetime):
            change_date = change_date.date()
        return await client.get(f"/getChangedCubeList/{change_date.isoformat()}")

    @staticmethod
    async def get_cube_metadata(client: AsyncClient, product_id: int) -> Response:
        """
        Args:
            client (AsyncClient): The HTTP client to use for the request.
            product_id (int): The ID of the product to retrieve metadata for.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.post("/getCubeMetadata", json=[{"productId": product_id}])

    @staticmethod
    async def get_series_info_from_cube_pid_coord(
        client: AsyncClient, product_id: int, coordinate: str
    ) -> Response:  # TODO: perhaps coord should be a class
        """
        Users can also request series metadata either by CubePidCoord or Vector as seen
        earlier using getSeriesInfoFromVector.

        Args:
            client (AsyncClient): The HTTP client to use for the request.
            product_id (int): The ID of the product to retrieve metadata for.
            coordinate (str): The coordinate to retrieve series information for.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.post(
            "/getSeriesInfoFromCubePidCoord",
            json=[{"productId": product_id, "coordinate": coordinate}],
        )

    @staticmethod
    async def get_series_info_from_vector(
        client: AsyncClient, vector_id: int
    ) -> Response:
        """
        Args:
            client (AsyncClient): The HTTP client to use for the request.
            vector_id (int): The ID of the vector to retrieve series information for.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.post(
            "/getSeriesInfoFromVector", json=[{"vectorId": vector_id}]
        )

    @staticmethod
    async def get_all_cubes_list(client: AsyncClient) -> Response:
        """
        Users can query the output database to provide a complete inventory of data
        tables available through this Statistics Canada API. This command accesses a
        comprehensive list of details about each table including information at the
        dimension level.

        Args:
            client (AsyncClient): The HTTP client to use for the request.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.get("/getAllCubesList")

    @staticmethod
    async def get_all_cubes_list_lite(client: AsyncClient) -> Response:
        """
        Users can query the output database to provide a complete inventory of data
        tables available through this Statistics Canada API. This command accesses a
        list of details about each table.  Unlike getAllCubesList, this method does not
        return dimension or footnote information.

        Args:
            client (AsyncClient): The HTTP client to use for the request.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.get("/getAllCubesListLite")

    @staticmethod
    async def get_changed_series_data_from_cube_pid_coord(
        client: AsyncClient, product_id: int, coordinate: str
    ) -> Response:
        """
        Args:
            client (AsyncClient): The HTTP client to use for the request.
            product_id (int): The ID of the product to retrieve metadata for.
            coordinate (str): The coordinate to retrieve series information for.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.post(
            "/getChangedSeriesDataFromCubePidCoord",
            json=[{"productId": product_id, "coordinate": coordinate}],
        )

    @staticmethod
    async def get_changed_series_data_from_vector(
        client: AsyncClient, vector_id: int
    ) -> Response:
        """
        Args:
            client (AsyncClient): The HTTP client to use for the request.
            vector_id (int): The ID of the vector to retrieve series information for.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.post(
            "/getChangedSeriesDataFromVector", json=[{"vectorId": vector_id}]
        )

    @staticmethod
    async def get_data_from_cube_pid_coord_and_latest_n_periods(
        client: AsyncClient, product_id: int, coordinate: str, n: int
    ) -> Response:
        """
        Args:
            client (AsyncClient): The HTTP client to use for the request.
            product_id (int): The ID of the product to retrieve metadata for.
            coordinate (str): The coordinate to retrieve series information for.
            n (int): The number of latest periods to retrieve.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.post(
            "/getDataFromCubePidCoordAndLatestNPeriods",
            json=[{"productId": product_id, "coordinate": coordinate, "latestN": n}],
        )

    @staticmethod
    async def get_data_from_vector_and_latest_n_periods(
        client: AsyncClient, vector_id: int, n: int
    ) -> Response:
        """
        Args:
            client (AsyncClient): The HTTP client to use for the request.
            vector_id (int): The ID of the vector to retrieve series information for.
            n (int): The number of latest periods to retrieve.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.post(
            "/getDataFromVectorsAndLatestNPeriods",
            json=[{"vectorId": vector_id, "latestN": n}],
        )

    @staticmethod
    async def get_bulk_vector_data_by_range(
        client: AsyncClient, vector_ids: list[int], start: datetime, end: datetime
    ) -> Response:
        """
        For users that require accessing data according to a certain date range, this
        method allows access by date range and vector.

        Args:
            client (AsyncClient): The HTTP client to use for the request.
            vector_ids (list[int]): The list of vector IDs to retrieve data for.
            start (datetime): The start date of the range.
            end (datetime): The end date of the range.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.post(
            url="/getBulkVectorDataByRange",
            json={
                "vectorIds": vector_ids,
                "startDataPointReleaseDate": start.isoformat(),
                "endDataPointReleaseDate": end.isoformat(),
            },
        )

    @staticmethod
    async def get_data_from_vector_by_reference_period_range(
        client: AsyncClient, vector_ids: list[int], start: date, end: date
    ) -> Response:
        """
        For users that require accessing data according to a certain reference period
        range, this method allows access by reference period range and vector.

        Args:
            client (AsyncClient): The HTTP client to use for the request.
            vector_ids (list[int]): The list of vector IDs to retrieve data for.
            start (date): The start date of the reference period.
            end (date): The end date of the reference period.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.get(
            url="/getDataFromVectorByReferencePeriodRange",
            params={
                "vectorIds": vector_ids,
                "startRefPeriod": start.isoformat(),
                "endDataPointReleaseDate": end.isoformat(),
            },
        )

    @staticmethod
    async def get_full_table_download_csv(
        client: AsyncClient, table_id: int, language: ResponseLanguage
    ) -> Response:
        """
        For users who require the full table/cube of extracted time series, a static
        file download is available via a return link. The CSV version also lets users
        select either the English (en) or French (fr) versions.

        Args:
            client (AsyncClient): The HTTP client to use for the request.
            table_id (int): The ID of the table to download.
            language (ResponseLanguage): The language version to download.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.get(f"/getFullTableDownloadCSV/{table_id}/{language.value}")

    @staticmethod
    async def get_full_table_download_sdmx(
        client: AsyncClient, table_id: int
    ) -> Response:
        """
        For users who require the full table/cube of extracted time series, a static
        file download is available via a return a link. For SDMX full table download,
        language selection is not required (bilingual format).

        Args:
            client (AsyncClient): The HTTP client to use for the request.
            table_id (int): The ID of the table to download.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.get(f"/getFullTableDownloadSDMX/{table_id}")

    @staticmethod
    async def get_code_sets(client: AsyncClient) -> Response:
        """
        Code Sets provide additional information to describe the information such as
        scales, frequencies and symbols. Use method getCodeSets to access the most
        recent version of the code sets with descriptions (English and French) for all
        possible codes.

        Args:
            client (AsyncClient): The HTTP client to use for the request.

        Returns:
            Response: The HTTP response from the WDS API.
        """
        return await client.get("/getCodeSets")
