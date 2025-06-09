from typing import Optional, Iterable
from pathlib import Path

import logging

import pandas as pd
from httpx import AsyncClient


DEFAULT_DATA_PATH = Path('data')
DEFAULT_ENCODINGS = ('latin1', 'utf-8', 'utf-16')

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