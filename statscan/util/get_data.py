from typing import Optional, Iterable, Any
from pathlib import Path
import mimetypes
from datetime import datetime, date

import logging

import pandas as pd
from httpx import AsyncClient, Response


from statscan.url import CENSUS_SDMX_BASE_URL, WDS_URL
from statscan.enums.wds.wds import Detail, Format, WDSDATAMIME, WDSMETADATAMIME
from statscan.enums.frequency import Frequency
from statscan.enums.stats_filter import StatsFilter


DEFAULT_DATA_PATH = Path('data')
DEFAULT_ENCODINGS = ('latin1', 'utf-8', 'utf-16')

DEFAULT_RESOURCE = 'data'
DEFAULT_AGENCY = 'STC_CP'


logger = logging.getLogger(__name__)


async def download_data(url: str, data_dir: Path = DEFAULT_DATA_PATH, file_name: Optional[str] = None, overwrite: bool = False) -> Path:
    """
    Download data from the specified URL and save it to the given path.
    
    Args:
        url (str): The URL to download data from.
        path (Path): The local path where the data will be saved.
    
    Returns:
        Path: The path to the downloaded data file.
    """
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
    if file_name is None:
        file_name = url.split('/')[-1]
    file_path = data_dir / file_name
    if file_path.exists():
        logger.warning(f"File {file_path} already exists. Skipping download.")
        return file_path
    else:
        logger.debug(f"Downloading data from {url} to {file_path}")
        async with AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            file_path.write_bytes(response.content)
        return file_path
    

def unpack_to_dataframe(file_path: Path, encodings: Iterable[str] = DEFAULT_ENCODINGS) -> pd.DataFrame:
    """
    Unzip a file and return its contents as a pandas DataFrame.
    
    Args:
        zip_path (Path): The path to the zip file.
    
    Returns:
        pd.DataFrame: The contents of the specified file as a DataFrame.
    """
    logger.debug(f'Unpacking file {file_path} to DataFrame')
    for enc in encodings:
        try:
            return pd.read_csv(file_path, dtype=str, encoding=enc)
        except ValueError as e:
            logger.error(f"Failed to read CSV with encoding {enc}: {type(e)} {e}")
    raise ValueError(f'Failed to read file "{file_path}"" with all provided encodings: {encodings}')


def make_key(frequency: Frequency, dguid: str | Iterable[str], stats_filter: Optional[StatsFilter]) -> str:
    """
    Create a key for the WDS API based on frequency and dguid.
    
    Args:
        frequency (Frequency): The frequency of the data.
        dguid (str | Iterable[str]): The dguid(s) to include in the key.
        stats_filter (StatsFilter, optional): Statistical filter for the statistics.
    
    Returns:
        str: The formatted key string.
        
    Note:
        This function is deprecated for SDMX usage. Use make_census_profile_key() instead
        for Census Profile SDMX API calls which require 5 dimensions.
    """
    stats_filter = stats_filter or StatsFilter()
    if not isinstance(dguid, str):
        dguid = '+'.join(dguid)
    return f'{frequency.name}.{dguid}.{stats_filter}'


def make_census_profile_key(
    dguid: str | Iterable[str], 
    frequency: Frequency = Frequency.A5,
    stats_filter: Optional[StatsFilter] = None,
    time_period: str = "2021",
    characteristic: str = "1", 
    gender_statistic: str = "1"
) -> str:
    """
    Create a 5-dimension key for the Census Profile SDMX API.
    
    The Census Profile SDMX API requires exactly 5 dimensions in this order:
    1. Reference Area (DGUID)
    2. Time Period (year)
    3. Frequency (e.g., A5 for annual) 
    4. Characteristic (statistic type)
    5. Gender/Statistic (demographic breakdown)
    
    Args:
        dguid (str | Iterable[str]): The DGUID(s) for geographic area(s).
        frequency (Frequency): The frequency (default: A5).
        stats_filter (StatsFilter, optional): Additional filter (currently unused).
        time_period (str): The time period/year (default: "2021").
        characteristic (str): The characteristic dimension (default: "1").
        gender_statistic (str): The gender/statistic dimension (default: "1").
        
    Returns:
        str: The 5-dimension key string (e.g., "2021A000535570.2021.A5.1.1").
        
    Examples:
        >>> make_census_profile_key("2021A000535570")
        "2021A000535570.2021.A5.1.1"
        
        >>> make_census_profile_key(["2021A000535570", "2021A000535571"])  
        "2021A000535570+2021A000535571.2021.A5.1.1"
    """
    # Handle multiple DGUIDs
    if not isinstance(dguid, str):
        dguid = '+'.join(dguid)
    
    # Build the 5-dimension key
    key_parts = [
        dguid,                    # Dimension 1: Reference Area (DGUID)
        time_period,              # Dimension 2: Time Period  
        frequency.name,           # Dimension 3: Frequency
        characteristic,           # Dimension 4: Characteristic
        gender_statistic          # Dimension 5: Gender/Statistic
    ]
    
    return '.'.join(key_parts)


async def get_sdmx_data(
    flow_ref: str,
    dguid: str | Iterable[str],
    frequency: Frequency = Frequency.A5,
    stats_filter: Optional[StatsFilter] = None,
    base_url: str = CENSUS_SDMX_BASE_URL,
    resource: str = DEFAULT_RESOURCE,
    agency: str = DEFAULT_AGENCY,
    detail: Optional[Detail] = None,
    format: Optional[Format] = None,
    parameters: Optional[dict[str, Any]] = None,
    timeout: Optional[float] = None,
    client_kwargs: Optional[dict[str, Any]] = None,
) -> Response:
    """
    Get SDMX data from the Census Profile SDMX API.
    
    Args:
        flow_ref (str): The dataflow reference to query (e.g., 'DF_CSD', 'DF_CD', 'DF_PR').
        dguid (str | Iterable[str]): The DGUID(s) for the geographic area(s).
        frequency (Frequency): The frequency of the data (default: A5 for annual).
        stats_filter (StatsFilter, optional): Statistical filter for additional dimensions.
        base_url (str): The base URL for the Census Profile SDMX API.
        resource (str): Deprecated - kept for compatibility but not used.
        agency (str): Deprecated - kept for compatibility but not used.
        detail (Detail, optional): The level of detail for the data.
        format (Format, optional): The format of the data to return.
        parameters (dict, optional): Additional query parameters.
        timeout (float, optional): Request timeout in seconds.
        client_kwargs (dict, optional): Additional arguments for the HTTP client.
        
    Returns:
        Response: The HTTP response containing SDMX data.
        
    Raises:
        HTTPError: If the API request fails.
        
    Note:
        This function uses the Statistics Canada Census Profile SDMX API which requires
        exactly 5 dimensions in the key. The API expects the following dimension order:
        1. Reference Area (DGUID)
        2. Time Period (year) 
        3. Frequency (e.g., A5)
        4. Characteristic (statistic type)
        5. Gender/Statistic (demographic breakdown)
        
        Available dataflows include:
        - DF_CSD: Census subdivisions
        - DF_CD: Census divisions  
        - DF_PR: Provinces/territories
        - DF_CMACA: Census metropolitan areas
        - And others (see get_dataflows() for complete list)
    """

    # Generate the 5-dimension key required by the Census Profile SDMX API
    key = make_census_profile_key(
        dguid=dguid, 
        frequency=frequency, 
        stats_filter=stats_filter
    )
    
    # Use the correct URL structure for Census Profile SDMX API
    url = f'{base_url}/data/{flow_ref}/{key}'

    # Add format/detail parameters if specified
    for p in (format, detail):
        if p is not None:
            parameters = p.add_to_params(parameters)

    client_kwargs = client_kwargs or {}
    if timeout is not None:
        client_kwargs['timeout'] = timeout

    logger.debug(f'Fetching Census Profile SDMX data from {url} with parameters {parameters}')
    async with AsyncClient(**client_kwargs) as client:  # type: ignore[arg-type]
        response = await client.get(url, params=parameters)
    response.raise_for_status()
    return response

async def get_codes(
    base_url: str = CENSUS_SDMX_BASE_URL,
    resource: str = 'CL_GEO_CMACA',
    agency: str = DEFAULT_AGENCY,
    content_type: str = mimetypes.types_map['.json'],
) -> Response:
    url = f'{base_url}/codelist/{agency}/{resource}/latest'
    logger.debug(f'Fetching codes from {url} with content type {content_type}')
    async with AsyncClient() as client:
        response = await client.get(url, headers={'Accept': content_type})
    response.raise_for_status()
    return response


async def get_dataflows(
    base_url: str = CENSUS_SDMX_BASE_URL,
    agency: str = DEFAULT_AGENCY,
    content_type: str = mimetypes.types_map['.json'],
) -> Response:
    """
    Get the available data flows from the WDS API.
    
    Returns:
        Response: The API response containing the data flows.
    """
    url = f'{base_url}/dataflow/{agency}/all/latest'
    logger.debug(f'Fetching data flows from {url}')
    async with AsyncClient() as client:
        response = await client.get(url, headers={'Accept': content_type})
    response.raise_for_status()
    return response


async def get_metadata(
    flow_ref: str,
    base_url: str = CENSUS_SDMX_BASE_URL,
    agency: str = DEFAULT_AGENCY,
    content_type: str = WDSMETADATAMIME.SDMX_JSON,
) -> Response:
    """
    Get metadata for a specific flow from the WDS API.
    Args:
        flow_ref (str): The flow reference to query.
        base_url (str): The base URL for the WDS API.
        agency (str): The agency to query.
        content_type (str): The content type for the response.
    Returns:
        Response: The API response containing the metadata.
    """
    url = f'{base_url}/dataflow/{agency}/{flow_ref}'
    parameters = {'references': 'all'}
    logger.debug(f'Fetching metadata from {url} with parameters {parameters} and content type {content_type}')
    async with AsyncClient() as client:
        response = await client.get(url, headers={'Accept': content_type}, params=parameters)
    response.raise_for_status()
    return response
