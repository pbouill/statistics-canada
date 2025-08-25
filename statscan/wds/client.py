from datetime import date, datetime
from typing import Iterable

from httpx import AsyncClient

from statscan.url import WDS_URL


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
    
    async def getChangedSeriesList(self) -> dict:
        """
        Query for what series have changed today. This can be invoked at any time of day and will reflect the list of series that have been updated at 8:30am EST on a given release up until midnight that same day.

        Returns:
            dict: A dictionary containing the list of changed series.
        """
        async with self.client as client:
            response = await client.get('/getChangedSeriesList')
        response.raise_for_status()
        return response.json()

    async def getChangedCubeList(self, change_date: datetime | date) -> dict:
        """
        Query what has changed at the table/cube level on a specific day. This date can be any date from today into the past.

        Args:
            change_date (datetime | date): The date to query for changes.
        Returns:
            dict: A dictionary containing the list of changed cubes.
        """
        if isinstance(change_date, datetime):
            change_date = change_date.date()
        async with self.client as client:
            response = await client.get(f'/getChangedCubeList/{change_date.isoformat()}')
        response.raise_for_status()
        return response.json()
    
    async def getCubeMetadata(self, product_id: int) -> dict:
        """
        Get metadata for a specific cube product ID.

        Args:
            product_id (int): The product ID of the cube.
        Returns:
            dict: The metadata for the cube.
        """
        async with self.client as client:
            response = await client.post(f'/getCubeMetadata', json=[{'productId': product_id}])
        response.raise_for_status()
        return response.json()
    
    async def getSeriesInfoFromCubePidCoord(self, product_id: int, coordinates: Iterable[int]) -> dict:
        """
        Get series information from a cube product ID and coordinates.
        
        Args:
            product_id (int): The product ID of the cube.
            coordinates (Iterable[int]): The coordinates to query.
        Returns:
            dict: The series information.
        """
        coordinate = '.'.join(map(str, coordinates))
        async with self.client as client:
            response = await client.post(f'/getSeriesInfoFromCubePidCoord', json=[{'productId': product_id, 'coordinate': coordinate}])
        response.raise_for_status()
        return response.json()
    
    async def getSeriesInfoFromVector(self, vectorId: int) -> dict:
        """
        Get series information from a vector ID.
        
        Args:
            vector_id (int): The vector ID to query.
        Returns:
            dict: The series information.
        """
        async with self.client as client:
            response = await client.post(f'/getSeriesInfoFromVector', json=[{'vectorId': vectorId}])
        response.raise_for_status()
        return response.json()
    
    async def getAllCubesList(self) -> dict:
        """
        Query the output database to provide a complete inventory of data tables available through this Statistics Canada API. 
        This command accesses a comprehensive list of details about each table including information at the dimension level.
        
        Returns:
            dict: A dictionary containing the list of all cubes.
        """
        async with self.client as client:
            response = await client.get('/getAllCubesList')
        response.raise_for_status()
        return response.json()
    
    async def getAllCubesListLite(self) -> dict:
        """
        Query the output database to provide a complete inventory of data tables available through this Statistics Canada API.
        This command accesses a comprehensive list of details about each table including information at the dimension level.
        
        Returns:
            dict: A dictionary containing the list of all cubes in a lightweight format.
        """
        async with self.client as client:
            response = await client.get('/getAllCubesListLite')
        response.raise_for_status()
        return response.json()
    

    async def getCodeSets(self) -> dict:
        """
        Get the code sets available in the WDS API.
        
        Returns:
            dict: A dictionary containing the code sets.
        """
        async with self.client as client:
            response = await client.get('/getCodeSets')
        response.raise_for_status()
        return response.json()