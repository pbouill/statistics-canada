"""Statistics Canada Web Data Service (WDS) API client implementation.

This module provides the main `Client` class for interacting with the WDS API,
supporting all documented endpoints including cube metadata, series data,
vector information, and geographic queries.

Official Documentation: https://www.statcan.gc.ca/en/developers/wds/user-guide
"""
import asyncio
import logging
import zipfile
from datetime import date, datetime
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Any, TypeVar

import httpx
import numpy as np
import pandas as pd
from httpx._client import AsyncClient, Timeout, TimeoutTypes

from statscan.enums.auto.wds.product_id import ProductID
from statscan.enums.auto.wds.scalar import Scalar
from statscan.enums.auto.wds.symbol import Symbol
from statscan.url import WDS_URL
from statscan.util.search import fuzzy_search_objects, get_match_details
from statscan.wds.cache import ResponseCache
from statscan.wds.models.code import CodeSets

from .coordinate import Coordinate, create_enhanced_demographic_dataframe
from .cube_manager import CubeManager
from .geographic import GeographicEntity
from .models.cube import Cube, CubeExistsError
from .models.datapoint import DataPoint
from .models.series import ChangedSeriesData, Series
from .models.vector import Vector
from .requests import ResponseLanguage, WDSRequests

# Timeout configuration with retry strategy for reliable operation
# Uses shorter base timeouts (30s) with automatic retry and exponential backoff
# to handle transient connection issues more gracefully than a single long timeout.
#
# Retry strategy (via retry_on_timeout in requests.py):
# - Attempt 1: 30s timeout
# - Attempt 2: 60s timeout (after 1s wait)
# - Attempt 3: 120s timeout (after 2s wait)
# Total max wait: ~213s (30+60+120+waits) vs 180s single timeout
#
# This approach provides:
# - Faster recovery from transient failures (DNS, TLS handshake delays)
# - Better user experience (fails fast, retries automatically)
# - Coverage for observed 121.64s Python 3.13 TLS issue
# - More resilient to intermittent network issues
DEFAULT_WDS_TIMEOUT = Timeout(
    connect=30.0,  # Base connection timeout - will retry with exponential backoff
    read=90.0,  # Read timeout - sufficient for large responses
    write=60.0,  # Write timeout - standard for POST requests
    pool=30.0,  # Pool timeout - connection pool management
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
        cache_path: str | Path | None = None,
        enable_cache: bool = True,
        **kwargs,
    ):
        """Initialize the WDS client (subclass of httpx.AsyncClient).

        The client automatically retries failed requests using exponential backoff:
        - Attempt 1: 30s connect timeout
        - Attempt 2: 60s connect timeout (after 1s wait)
        - Attempt 3: 120s connect timeout (after 2s wait)

        This provides reliable operation while handling transient connection issues
        more gracefully than a single long timeout.

        Args:
            base_url: The base URL for the WDS API. Defaults to WDS_URL.
            timeout: The timeout configuration to use when sending requests.
                Defaults to 30s base connect timeout with exponential backoff retry.
            http2: Enable HTTP/2 support. Defaults to False for reliability.
            cache_path: Path to SQLite cache file for HTTP responses.
                If None, uses a temp file. Set to False to disable caching entirely.
            enable_cache: Whether to enable HTTP response caching. Defaults to True.
                When enabled, API responses are cached to minimize redundant requests.
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
        self._max_retries = 3
        self._backoff_multiplier = 2.0

        # Initialize HTTP response cache
        self.cache = ResponseCache(cache_path=cache_path, enabled=enable_cache)

        super().__init__(base_url=base_url, timeout=timeout, http2=http2, **kwargs)

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Execute an HTTP request with exponential backoff retry on timeout.

        This method implements automatic retry logic for transient connection
        failures (DNS delays, TLS handshake timeouts, temporary network issues).

        Retry strategy with base timeout of 30s:
        - Attempt 1: 30s timeout
        - Attempt 2: 60s timeout (2x multiplier, after 1s wait)
        - Attempt 3: 120s timeout (4x multiplier, after 2s wait)

        This covers the observed 121.64s Python 3.13 TLS failure while providing
        faster recovery from transient issues.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments passed to the request method

        Returns:
            Response object from httpx

        Raises:
            httpx.TimeoutException: If all retry attempts fail
            httpx.HTTPStatusError: On HTTP errors (4xx, 5xx)

        """
        last_exception: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            # Calculate timeout for this attempt with exponential backoff
            if isinstance(self.timeout, Timeout):
                timeout_multiplier = self._backoff_multiplier ** (attempt - 1)
                # Handle None values in timeout components
                connect_timeout = (
                    self.timeout.connect * timeout_multiplier
                    if self.timeout.connect is not None
                    else None
                )
                current_timeout = Timeout(
                    connect=connect_timeout,
                    read=self.timeout.read,
                    write=self.timeout.write,
                    pool=self.timeout.pool,
                )
            else:
                current_timeout = self.timeout

            try:
                logger.debug(
                    f"Request attempt {attempt}/{self._max_retries}: "
                    f"{method} {url} (timeout: {current_timeout.connect}s connect)"
                )

                # Make the request with the current timeout
                request_method = getattr(super(), method.lower())
                response = await request_method(url, timeout=current_timeout, **kwargs)
                return response

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.PoolTimeout) as e:
                last_exception = e
                logger.warning(
                    f"Timeout on attempt {attempt}/{self._max_retries}: {e}"
                )

                if attempt < self._max_retries:
                    # Wait before retry with increasing delay
                    wait_time = 1.0 * attempt  # 1s, 2s
                    logger.info(f"Waiting {wait_time:.0f}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"All {self._max_retries} attempts failed: {e}")
                    raise

            except Exception as e:
                # Don't retry on non-timeout errors (4xx, 5xx, etc.)
                logger.error(f"Non-retryable error: {e}")
                raise

        # Should never reach here, but just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected state in _request_with_retry")

    async def get(self, url: str, **kwargs) -> httpx.Response:  # type: ignore[override]
        """Send GET request with automatic retry on timeout and caching.

        Checks cache first before making the actual request. Successful responses
        (status 200-299) are automatically cached for future use.

        Args:
            url: URL to request
            **kwargs: Additional arguments passed to httpx.AsyncClient.get
                     Includes params, headers, etc.

        Returns:
            Response object (either from cache or fresh request)

        """
        # Extract params for cache key
        params = kwargs.get('params')

        # Check cache first
        cached = self.cache.get(method="GET", url=url, params=params)
        if cached:
            # Reconstruct response from cached data
            # Remove content-encoding headers since we store decompressed content
            headers = cached["headers"].copy()
            headers.pop("content-encoding", None)
            headers.pop("content-length", None)  # Will be recalculated

            # Create a request object for the response
            # This is needed for raise_for_status() to work properly
            request = httpx.Request(
                method="GET",
                url=url,
                params=params,
            )

            return httpx.Response(
                status_code=cached["status_code"],
                headers=headers,
                content=cached["content"],
                request=request,
            )

        # Cache miss - make the request
        response = await self._request_with_retry("GET", url, **kwargs)

        # Cache successful responses (2xx status codes)
        if HTTPStatus.OK <= response.status_code < HTTPStatus.MULTIPLE_CHOICES:
            self.cache.put(
                method="GET",
                url=url,
                response_data=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                params=params,
            )

        return response

    async def post(self, url: str, **kwargs) -> httpx.Response:  # type: ignore[override]
        """Send POST request with automatic retry on timeout and caching.

        Checks cache first before making the actual request. Successful responses
        (status 200-299) are automatically cached for future use.

        Args:
            url: URL to request
            **kwargs: Additional arguments passed to httpx.AsyncClient.post
                     Includes data, json, headers, etc.

        Returns:
            Response object (either from cache or fresh request)

        """
        # Extract data/json for cache key
        data = kwargs.get('data') or kwargs.get('json')
        params = kwargs.get('params')

        # Check cache first
        cached = self.cache.get(method="POST", url=url, params=params, data=data)
        if cached:
            # Reconstruct response from cached data
            # Remove content-encoding headers since we store decompressed content
            headers = cached["headers"].copy()
            headers.pop("content-encoding", None)
            headers.pop("content-length", None)  # Will be recalculated

            # Create a request object for the response
            # This is needed for raise_for_status() to work properly
            request = httpx.Request(
                method="POST",
                url=url,
                params=params,
                json=kwargs.get('json'),
                data=kwargs.get('data'),
            )

            return httpx.Response(
                status_code=cached["status_code"],
                headers=headers,
                content=cached["content"],
                request=request,
            )

        # Cache miss - make the request
        response = await self._request_with_retry("POST", url, **kwargs)

        # Cache successful responses (2xx status codes)
        if HTTPStatus.OK <= response.status_code < HTTPStatus.MULTIPLE_CHOICES:
            self.cache.put(
                method="POST",
                url=url,
                response_data=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                params=params,
                data=data,
            )

        return response

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

    async def update_cube(self, product_id: int | ProductID) -> Cube:
        """Update or add a specific cube by its product ID.

        Args:
            product_id: The product ID (int or ProductID enum).

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

    async def get_cube_metadata(self, product_id: int | ProductID) -> Cube:
        """Get metadata for a specific cube product ID.

        Args:
            product_id: The product ID of the cube (int or ProductID enum).

        Returns:
            The Cube object populated with the returned metadata.

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        coro = WDSRequests.get_cube_metadata(client=self, product_id=pid)
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

    async def _validate_coordinate(
        self,
        product_id: int | ProductID,
        coordinate: str | Coordinate,
        strict: bool = True,
    ) -> tuple[bool, str]:
        """Validate a coordinate against cube metadata.

        Fetches cube metadata if not already cached, then validates the
        coordinate structure and member IDs.

        Args:
            product_id: The product ID of the cube (int or ProductID enum).
            coordinate: The coordinate string or Coordinate object to validate.
            strict: If True, raises ValueError on invalid coordinate.
                If False, returns validation result as tuple.

        Returns:
            A tuple of (is_valid, error_message). If strict=True and invalid,
            raises ValueError instead.

        Raises:
            ValueError: If strict=True and coordinate is invalid.

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        # Try to get cube from cache first
        cube = self.cube_manager.cubes.get(pid)

        # If not cached, fetch it
        if not cube:
            cube = await self.get_cube_metadata(pid)
            self.cube_manager.add_cube(cube, replace=True)

        # Validate the coordinate
        is_valid, error_msg = cube.validate_coordinate(coordinate)

        if not is_valid and strict:
            raise ValueError(
                f"Invalid coordinate for product {pid}: {error_msg}"
            )

        return is_valid, error_msg

    async def _check_coordinate_support(
        self,
        product_id: int | ProductID,
    ) -> None:
        """Check if cube supports coordinate queries and raise error if not.

        Args:
            product_id: The product ID of the cube (int or ProductID enum).

        Raises:
            ValueError: If cube doesn't support coordinate-based queries.

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        # Try to get cube from cache first
        cube = self.cube_manager.cubes.get(pid)

        # If not cached, fetch it
        if not cube:
            cube = await self.get_cube_metadata(pid)
            self.cube_manager.add_cube(cube, replace=True)

        # Check if cube supports coordinate queries
        if not cube.supports_coordinate_queries:
            raise ValueError(
                f"Cube {pid} does not support coordinate-based queries. "
                f"This appears to be a snapshot cube (census, one-time survey, etc.). "
                f"Use get_dataframe() to download and filter the complete table, or "
                f"get_full_table_download_csv() for the raw download URL."
            )

    async def get_series_info_from_cube_pid_coord(
        self,
        product_id: int | ProductID,
        coordinate: str | Coordinate,
        validate: bool = True,
    ) -> Series:
        """Get series information from a cube product ID and coordinate.

        Args:
            product_id: The product ID of the cube (int or ProductID enum).
            coordinate: The coordinate string or Coordinate object.
            validate: If True, validates coordinate against cube metadata
                before making the API request.

        Returns:
            The Series object populated with the returned information.

        Raises:
            ValueError: If validate=True and coordinate is invalid, or if
                the cube doesn't support coordinate-based queries.

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        # Check if cube supports coordinate queries
        await self._check_coordinate_support(pid)

        # Validate coordinate if requested
        if validate:
            await self._validate_coordinate(pid, coordinate, strict=True)

        coro = WDSRequests.get_series_info_from_cube_pid_coord(
            client=self, product_id=pid, coordinate=str(coordinate)
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
        self,
        product_id: int | ProductID,
        coordinate: str | Coordinate,
        validate: bool = True,
    ) -> Series:
        """Get changed series data from a cube product ID and coordinate.

        Args:
            product_id: The product ID of the cube (int or ProductID enum).
            coordinate: The coordinate to query.
            validate: If True, validates coordinate against cube metadata
                before making the API request.

        Returns:
            Series: The Series object populated with the returned information.

        Raises:
            ValueError: If validate=True and coordinate is invalid, or if
                the cube doesn't support coordinate-based queries.

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        # Check if cube supports coordinate queries
        await self._check_coordinate_support(pid)

        # Validate coordinate if requested
        if validate:
            await self._validate_coordinate(pid, coordinate, strict=True)

        coro = WDSRequests.get_changed_series_data_from_cube_pid_coord(
            client=self, product_id=pid, coordinate=str(coordinate)
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
        self,
        product_id: int | ProductID,
        coordinate: str | Coordinate,
        n: int,
        validate: bool = True,
    ) -> ChangedSeriesData:
        """Get data from a cube product ID, coordinate, and latest N periods.

        Args:
            product_id: The product ID of the cube (int or ProductID enum).
            coordinate: The coordinate to query.
            n: The number of latest periods to retrieve.
            validate: If True, validates coordinate against cube metadata
                before making the API request.

        Returns:
            The ChangedSeriesData object populated with the returned info.

        Raises:
            ValueError: If validate=True and coordinate is invalid, or if
                the cube doesn't support coordinate-based queries.

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        # Check if cube supports coordinate queries
        await self._check_coordinate_support(pid)

        # Validate coordinate if requested
        if validate:
            await self._validate_coordinate(pid, coordinate, strict=True)

        coro = WDSRequests.get_data_from_cube_pid_coord_and_latest_n_periods(
            client=self, product_id=pid, coordinate=str(coordinate), n=n
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

    async def get_full_table_download_csv(
        self,
        product_id: int | ProductID,
        language: ResponseLanguage = ResponseLanguage.EN,
    ) -> str:
        """Get download URL for full table/cube as CSV.

        For tables that don't support coordinate-based queries (e.g., census
        cubes), this method provides a URL to download the complete table data.
        Particularly useful for snapshot cubes where coordinate queries return
        406 errors.

        Args:
            product_id: The product ID of the table (int or ProductID enum).
            language: The language for the CSV (EN or FR). Defaults to EN.

        Returns:
            str: The download URL for the CSV file.

        Example:
            >>> client = Client()
            >>> # Census cube - doesn't support coordinates
            >>> url = await client.get_full_table_download_csv(98100001)
            >>> print(f"Download: {url}")

        Note:
            The returned URL is a direct download link to a CSV file.
            You can use this with pandas, requests, or other download tools.

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        coro = WDSRequests.get_full_table_download_csv(
            client=self, table_id=pid, language=language
        )
        response = await coro

        # The API returns a JSON response with status and download URL
        data = response.json()
        if isinstance(data, dict):
            # Response format: {"status": "SUCCESS", "object": "url"}
            status = data.get("status")
            obj = data.get("object")

            if status == "SUCCESS" and obj and isinstance(obj, str):
                return obj

            raise ValueError(
                f"API returned status '{status}' for product {pid}"
            )

        raise ValueError(
            f"Unexpected response format for product {pid}: {type(data)}"
        )

    async def get_full_table_download_sdmx(
        self,
        product_id: int | ProductID,
    ) -> str:
        """Get download URL for full table/cube as SDMX.

        For tables that don't support coordinate-based queries (e.g., census
        cubes), this method provides a URL to download the complete table data
        in SDMX format (bilingual, doesn't require language selection).

        Args:
            product_id: The product ID of the table (int or ProductID enum).

        Returns:
            str: The download URL for the SDMX file.

        Example:
            >>> client = Client()
            >>> # Census cube - doesn't support coordinates
            >>> url = await client.get_full_table_download_sdmx(98100001)
            >>> print(f"Download: {url}")

        Note:
            SDMX format is bilingual and structured for data exchange.
            The returned URL is a direct download link.

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        coro = WDSRequests.get_full_table_download_sdmx(client=self, table_id=pid)
        response = await coro

        # The API returns a JSON response with status and download URL
        data = response.json()
        if isinstance(data, dict):
            # Response format: {"status": "SUCCESS", "object": "url"}
            status = data.get("status")
            obj = data.get("object")

            if status == "SUCCESS" and obj and isinstance(obj, str):
                return obj

            raise ValueError(
                f"API returned status '{status}' for product {pid}"
            )

        raise ValueError(
            f"Unexpected response format for product {pid}: {type(data)}"
        )

    async def get_dataframe(
        self,
        product_id: int | ProductID,
        language: ResponseLanguage = ResponseLanguage.EN,
        **filters: str,
    ) -> pd.DataFrame:
        """Get complete table data as a pandas DataFrame with optional fuzzy filtering.

        This method downloads the full table CSV for any cube type (snapshot or
        time-series) and loads it directly into a pandas DataFrame. You can optionally
        filter the results using fuzzy matching on any column.

        Works for:
            - Snapshot cubes (census, one-time surveys)
            - Time-series cubes (CPI, labour force, GDP, etc.)

        Args:
            product_id: The product ID of the table (int or ProductID enum).
            language: The language for the data (EN or FR). Defaults to EN.
            **filters: Optional keyword arguments for fuzzy filtering.
                      Keys are matched against column names using fuzzy search.
                      Values are matched against column values using fuzzy search.
                      Example: geography="Saugeen Shores", characteristic="Population"

        Returns:
            pd.DataFrame: The complete (or filtered) table data as a pandas DataFrame.

        Example:
            >>> client = Client()
            >>> # Get all census data
            >>> df = await client.get_dataframe(98100002)
            >>> print(df.head())
            >>>
            >>> # Get census data filtered by geography (fuzzy match)
            >>> df = await client.get_dataframe(
            ...     98100002,
            ...     geography="Saugeen Shores"  # Handles typos like "Saugen Shore"
            ... )
            >>> print(df.head())
            >>>
            >>> # Multiple filters with fuzzy matching
            >>> df = await client.get_dataframe(
            ...     98100002,
            ...     geo="Toronto",  # Fuzzy matches "GEO" column
            ...     characteristic="population"  # Fuzzy matches characteristic values
            ... )

        Note:
            - The CSV files are compressed (.zip format)
            - Pandas automatically handles decompression from URLs
            - For large tables, this may take some time to download
            - Fuzzy filtering uses a 0.6 similarity threshold
            - Column names are matched first, then row values are filtered
            - For selective data access on time-series cubes, consider using
              coordinate-based query methods instead

        Raises:
            ValueError: If the download URL cannot be retrieved or loading fails.
            ValueError: If a filter key doesn't match any column (below threshold).

        """
        # Convert ProductID enum to int if needed
        pid = product_id.value if isinstance(product_id, ProductID) else product_id

        # Get the download URL for full table CSV
        url = await self.get_full_table_download_csv(
            product_id=pid,
            language=language
        )

        # Download and load the CSV into a DataFrame
        # The ZIP contains two files: {pid}.csv (data) and {pid}_MetaData.csv
        # We want the main data file, not the metadata

        try:
            # Download the ZIP file
            response = await self.get(url)
            zip_data = BytesIO(response.content)

            # Open and read the main CSV file (not the metadata)
            with zipfile.ZipFile(zip_data) as z:
                # Get the data file (the one without "_MetaData" in name)
                files = z.namelist()
                data_file = [
                    f for f in files
                    if "_MetaData" not in f and f.endswith(".csv")
                ][0]

                with z.open(data_file) as f:
                    # French CSVs use semicolon delimiter, English use comma
                    # Use UTF-8 encoding and handle potential BOM
                    delimiter = ";" if language == ResponseLanguage.FR else ","
                    df = pd.read_csv(
                        f,
                        encoding='utf-8-sig',
                        low_memory=False,
                        sep=delimiter
                    )

                    # Apply fuzzy filters if provided
                    if filters:
                        df = self._apply_fuzzy_filters(df, filters)

                    return df
        except Exception as e:
            raise ValueError(
                f"Failed to load DataFrame from {url}: {e}"
            ) from e

    def _apply_fuzzy_filters(
        self,
        df: pd.DataFrame,
        filters: dict[str, str],
    ) -> pd.DataFrame:
        """Apply fuzzy filters to a DataFrame.

        Args:
            df: The DataFrame to filter
            filters: Dictionary of column_key: value_to_match

        Returns:
            Filtered DataFrame

        Raises:
            ValueError: If a filter key doesn't match any column

        """
        filtered_df = df.copy()

        for filter_key, filter_value in filters.items():
            # Step 1: Fuzzy match the column name
            # Use lower cutoff for columns since they're often abbreviated
            column_matches = get_match_details(
                query=filter_key,
                candidates=df.columns.tolist(),
                n=3,  # Get top 3 to check for ambiguity
                cutoff=0.6
            )

            if not column_matches:
                raise ValueError(
                    f"Filter key '{filter_key}' didn't match any columns. "
                    f"Available columns: {', '.join(df.columns.tolist())}"
                )

            matched_column, column_score = column_matches[0]

            # Warn if there are other close matches (ambiguity)
            if len(column_matches) > 1:
                close_matches = [
                    (col, score) for col, score in column_matches[1:]
                    if score >= column_score - 0.1  # Within 0.1 of best score
                ]
                if close_matches:
                    close_str = ', '.join(
                        f'{col} ({score:.3f})' for col, score in close_matches
                    )
                    logger.warning(
                        f"Filter key '{filter_key}' has ambiguous matches: "
                        f"using '{matched_column}' (score: {column_score:.3f}), "
                        f"but also found: {close_str}"
                    )

            logger.info(
                f"Fuzzy matched filter key '{filter_key}' to column "
                f"'{matched_column}' (score: {column_score:.3f})"
            )

            # Step 2: Fuzzy match the value within that column
            # Get unique values in the column (as strings)
            unique_values = filtered_df[matched_column].astype(str).unique().tolist()

            value_matches = get_match_details(
                query=filter_value,
                candidates=unique_values,
                n=3,  # Get top 3 to check for ambiguity
                cutoff=0.6
            )

            if not value_matches:
                logger.warning(
                    f"Filter value '{filter_value}' didn't match any values in "
                    f"column '{matched_column}'. Trying substring match..."
                )
                # Fall back to substring matching
                mask = filtered_df[matched_column].astype(str).str.contains(
                    filter_value, case=False, na=False
                )
                filtered_df = filtered_df[mask]
            else:
                matched_value, value_score = value_matches[0]

                # Warn if there are other close matches (ambiguity)
                if len(value_matches) > 1:
                    close_matches = [
                        (val, score) for val, score in value_matches[1:]
                        if score >= value_score - 0.1  # Within 0.1 of best score
                    ]
                    if close_matches:
                        close_str = ', '.join(
                            f'{val} ({score:.3f})' for val, score in close_matches
                        )
                        logger.warning(
                            f"Filter value '{filter_value}' has ambiguous matches: "
                            f"using '{matched_value}' (score: {value_score:.3f}), "
                            f"but also found: {close_str}"
                        )

                logger.info(
                    f"Fuzzy matched filter value '{filter_value}' to "
                    f"'{matched_value}' (score: {value_score:.3f})"
                )

                # Filter rows where the column value matches
                filtered_df = filtered_df[
                    filtered_df[matched_column].astype(str) == matched_value
                ]

        logger.info(
            f"Fuzzy filtering: {len(df)} rows → {len(filtered_df)} rows "
            f"({len(filters)} filter(s) applied)"
        )

        return filtered_df

    # =======================
    # Cache Management Methods
    # =======================

    def clear_cache(self) -> int:
        """Clear all cached HTTP responses.

        Returns:
            int: Number of cache entries removed.

        Example:
            >>> client = Client()
            >>> count = client.clear_cache()
            >>> print(f"Cleared {count} cached responses")

        """
        return self.cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the HTTP response cache.

        Returns:
            dict: Cache statistics including:
                - total_entries: Number of cached responses
                - total_accesses: Total number of cache hits
                - cache_size_mb: Total size of cache in megabytes
                - oldest_entry: Timestamp of oldest cached entry
                - newest_entry: Timestamp of newest cached entry
                - most_accessed_url: URL with most cache hits

        Example:
            >>> client = Client()
            >>> stats = client.get_cache_stats()
            >>> print(f"Cache has {stats['total_entries']} entries")
            >>> print(f"Cache size: {stats['cache_size_mb']:.2f} MB")

        """
        return self.cache.get_stats()

    def list_cached_responses(self) -> list[dict[str, Any]]:
        """List all cached HTTP responses with metadata.

        Returns:
            list[dict]: List of cache entries, each containing:
                - method: HTTP method (GET/POST)
                - url: Request URL
                - status_code: HTTP status code
                - content_length: Size of cached content
                - created_at: When the entry was cached
                - accessed_at: Last access timestamp
                - access_count: Number of times accessed

        Example:
            >>> client = Client()
            >>> cached = client.list_cached_responses()
            >>> for entry in cached:
            ...     print(f"{entry['method']} {entry['url']}: "
            ...           f"{entry['content_length']} bytes, "
            ...           f"accessed {entry['access_count']} times")

        """
        return self.cache.list_cached_urls()

    async def aclose(self) -> None:
        """Close the HTTP client connection.

        Note:
            This closes the HTTP connection but does NOT delete the cache.
            The cache persists across multiple client instances to enable
            data reuse. Temp cache files are only cleaned up when the
            client object is garbage collected (script exit) or when
            clear_cache() is explicitly called.

        Example:
            >>> # Cache persists across context managers
            >>> async with Client() as client:
            ...     df1 = await client.get_dataframe(...)  # Downloads
            >>>
            >>> async with Client() as client:  # Same cache!
            ...     df2 = await client.get_dataframe(...)  # Cached

        """
        # Only close the HTTP client, not the cache
        # Cache persists for reuse across client instances
        await super().aclose()

    def __del__(self):
        """Cleanup on garbage collection - close cache and remove temp files."""
        # Close cache which will delete temp files if applicable
        if hasattr(self, 'cache') and self.cache:
            self.cache.close()

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

    # =======================
    # Fuzzy Search Methods
    # =======================

    def search_products(
        self,
        query: str,
        n: int = 10,
        cutoff: float = 0.4,
        search_in: str = "name",
    ) -> list[tuple[ProductID, float]]:
        """Search for WDS products using fuzzy matching.

        Searches through all available ProductID enums to find matches for
        the query string. Useful for discovering relevant data products when
        you don't know the exact name or ID.

        Args:
            query: Search term (e.g., "population", "CPI", "labour").
            n: Maximum number of results to return. Defaults to 10.
            cutoff: Minimum similarity score (0.0-1.0). Lower = more matches.
                Defaults to 0.4 (permissive for product discovery).
            search_in: Where to search - "name" (enum name), "value" (product
                ID number), or "both". Defaults to "name".

        Returns:
            List of (ProductID, score) tuples, sorted by relevance.

        Examples:
            >>> client = Client()
            >>> # Search for population products
            >>> results = client.search_products("population", n=5)
            >>> for product, score in results:
            ...     print(f"{score:.2f}: {product.name} ({product.value})")
            >>>
            >>> # Search for CPI products
            >>> results = client.search_products("consumer price", n=3)
            >>>
            >>> # Search by product ID
            >>> results = client.search_products("98100001", search_in="value")

        """
        # Get all ProductID enum members
        all_products = list(ProductID)

        # Define key function based on search_in parameter
        def _get_search_key(product: ProductID) -> str:
            if search_in == "name":
                # Search in enum names (e.g., "CONSUMER_PRICE_INDEX_MONTHLY")
                return product.name.replace("_", " ")
            if search_in == "value":
                # Search in product IDs (e.g., "18100004")
                return str(product.value)
            # "both" - search in combined name + value
            return f"{product.name.replace('_', ' ')} {product.value}"

        # Perform fuzzy search
        results = fuzzy_search_objects(
            query, all_products, key_func=_get_search_key, n=n, cutoff=cutoff
        )

        return results

    async def search_cubes(
        self,
        query: str,
        n: int = 10,
        cutoff: float = 0.4,
        language: ResponseLanguage = ResponseLanguage.EN,
    ) -> list[tuple[int, str, float]]:
        """Search for cubes by title using fuzzy matching.

        Fetches available cubes and searches their titles for matches.
        More expensive than search_products() as it requires an API call,
        but searches actual cube titles instead of enum names.

        Args:
            query: Search term (e.g., "census", "employment", "GDP").
            n: Maximum number of results to return. Defaults to 10.
            cutoff: Minimum similarity score (0.0-1.0). Defaults to 0.4.
            language: Language for cube titles (EN or FR).

        Returns:
            List of (product_id, title, score) tuples, sorted by relevance.

        Examples:
            >>> client = Client()
            >>> # Search for census cubes
            >>> results = await client.search_cubes("census population")
            >>> for pid, title, score in results:
            ...     print(f"{score:.2f}: [{pid}] {title}")
            >>>
            >>> # Search in French
            >>> results = await client.search_cubes(
            ...     "population", language=ResponseLanguage.FR
            ... )

        Note:
            This method makes an API call to fetch cube list. Results are
            not cached. For offline search, use search_products() instead.

        """
        # Get list of all cubes from WDS API
        # Note: This could be enhanced with caching in the future
        cubes_response = await WDSRequests.get_all_cubes_list_lite(client=self)

        # Extract cube information
        # The response structure may vary - adapt as needed
        if hasattr(cubes_response, "cubes"):
            cubes = cubes_response.cubes
        else:
            # Fallback if structure is different
            cubes = cubes_response

        # Build searchable list of (product_id, title) tuples
        cube_info = []
        for cube in cubes:
            product_id = (
                cube.productId
                if hasattr(cube, "productId")
                else cube.get("productId")
            )
            title = (
                cube.cubeTitleEn
                if language == ResponseLanguage.EN
                else cube.cubeTitleFr
            ) if hasattr(cube, "cubeTitleEn") else (
                cube.get(
                    "cubeTitleEn" if language == ResponseLanguage.EN else "cubeTitleFr"
                )
            )
            if product_id and title:
                cube_info.append((product_id, title))

        # Perform fuzzy search on titles
        results = fuzzy_search_objects(
            query,
            cube_info,
            key_func=lambda x: x[1],  # Search in title
            n=n,
            cutoff=cutoff,
        )

        # Return as (product_id, title, score) tuples
        return [(pid, title, score) for (pid, title), score in results]

    def search_dimension_members(
        self,
        cube: Cube,
        dimension_id: int,
        query: str,
        n: int = 5,
        cutoff: float = 0.6,
    ) -> list[tuple[int, str, float]]:
        """Search for dimension members using fuzzy matching.

        Searches through the members of a specific dimension to find matches.
        Useful for building coordinates when you don't know exact member IDs.

        Args:
            cube: The Cube object containing dimension information.
            dimension_id: Position ID of the dimension to search (1-based).
            query: Search term (e.g., "Toronto", "All items", "Canada").
            n: Maximum number of results to return. Defaults to 5.
            cutoff: Minimum similarity score (0.0-1.0). Defaults to 0.6.

        Returns:
            List of (member_id, member_name, score) tuples, sorted by score.

        Examples:
            >>> client = Client()
            >>> cube = await client.get_cube_metadata(18100004)  # CPI
            >>>
            >>> # Search for geographic dimension (dimension 1)
            >>> results = client.search_dimension_members(
            ...     cube, dimension_id=1, query="Canada"
            ... )
            >>> for member_id, name, score in results:
            ...     print(f"{score:.2f}: [{member_id}] {name}")
            >>>
            >>> # Search for products dimension
            >>> results = client.search_dimension_members(
            ...     cube, dimension_id=2, query="All items"
            ... )

        """
        # Get the dimension
        dimension = cube.get_dimension(dimension_id)
        if not dimension:
            raise ValueError(
                f"Dimension {dimension_id} not found in cube {cube.productId}"
            )

        if not dimension.member:
            raise ValueError(f"Dimension {dimension_id} has no members")

        # Build searchable list
        members = [
            (m.memberId, m.memberNameEn)
            for m in dimension.member
            if m.memberNameEn
        ]

        # Perform fuzzy search
        results = fuzzy_search_objects(
            query,
            members,
            key_func=lambda x: x[1],  # Search in member name
            n=n,
            cutoff=cutoff,
        )

        # Return as (member_id, name, score) tuples
        return [(mid, name, score) for (mid, name), score in results]

    def search_geographic_entities(
        self,
        query: str,
        n: int = 10,
        cutoff: float = 0.6,
    ) -> list[tuple[str, str, float]]:
        """Search for geographic entities using fuzzy matching.

        Searches through census geographic entities (from census subdivision
        product) to find municipalities, cities, towns, etc.

        Args:
            query: Search term (e.g., "Toronto", "Saugeen Shores").
            n: Maximum number of results to return. Defaults to 10.
            cutoff: Minimum similarity score (0.0-1.0). Defaults to 0.6.

        Returns:
            List of (name, dguid, score) tuples, sorted by relevance.

        Examples:
            >>> client = Client()
            >>> # Search for a municipality
            >>> results = await client.search_geographic_entities("Saugeen")
            >>> for name, dguid, score in results:
            ...     print(f"{score:.2f}: {name} ({dguid})")

        Note:
            This method requires downloading census subdivision data, which
            includes 5,468 municipalities (~4.6 MB, ~0.4s download).
            Consider caching the DataFrame if making multiple searches.

        """
        # This would need to be async and download the census data
        # For now, returning a placeholder
        raise NotImplementedError(
            "search_geographic_entities is not yet implemented. "
            "Use the standalone fuzzy search functions with "
            "census DataFrame instead. See examples in "
            "scratch/saugeen_with_fuzzy_search.py"
        )

