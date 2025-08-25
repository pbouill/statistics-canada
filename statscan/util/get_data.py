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
    
    Returns:
        str: The formatted key string.
    """
    stats_filter = stats_filter or StatsFilter()
    if not isinstance(dguid, str):
        dguid = '+'.join(dguid)
    return f'{frequency.name}.{dguid}.{stats_filter}'


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
    Get SDMX data from the WDS API.
    
    Args:
        flow_ref (str | Iterable[str]): The flow reference(s) to query.
        dguid (str | Iterable[str]): The dguid(s) for the data.
        stats_filter (StatsFilter, optional): Statistical filter for the statistics.
        base_url (str): The base URL for the WDS API.
        resource (str): The resource to query.
        agency (str): The agency to query.
        detail (Detail, optional): The level of detail for the data.
        format (Format, optional): The format of the data to return.
    Returns:
        dict[str, Any]: The SDMX data as a dictionary.
    """

    stats_filter = stats_filter or StatsFilter()
    key = make_key(frequency=frequency, dguid=dguid, stats_filter=stats_filter)
    url = f'{base_url}/{resource}/{agency},{flow_ref}/{key}'

    for p in (format, detail):
        if p is not None:
            parameters = p.add_to_params(parameters)

    client_kwargs = client_kwargs or {}
    if timeout is not None:
        client_kwargs['timeout'] = timeout

    logger.debug(f'Fetching SDMX data from {url} with parameters {parameters}')
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
