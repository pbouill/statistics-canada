from typing import Optional, Self, Any
from dataclasses import dataclass

from statscan.enums.schema import Schema
from statscan.enums.vintage import Vintage
from statscan.enums.frequency import Frequency
from statscan.enums.geocode.geocode import GeoCode
from statscan.enums.stats_filter import StatsFilter
from statscan.enums.wds import Detail, Format
from statscan.enums.auto import get_geocode_from_str
from statscan.util.get_data import get_sdmx_data, make_key
# Add imports for enhanced response handling
from statscan.data_response import CensusDataResponse, CensusDataFrame


@dataclass
class DGUID:
    '''
    Data Geographic Unique Identifier (DGUID) for StatsCan datasets.
    see: https://www12.statcan.gc.ca/wds-sdw/2021profile-profil2021-eng.cfm
    '''
    geocode: GeoCode
    vintage: Vintage = Vintage.CENSUS_2021  # Default vintage is Census 2021
    # frequency: Frequency = Frequency.A5  # Default frequency is every 5 years

    @property
    def schema(self) -> Schema:
        """
        Get the schema for the DGUID.
        
        Returns
        -------
        Schema
            The schema associated with the DGUID.
        """
        return self.geocode.schema
    
    @property
    def data_flow(self) -> str:
        """
        Get the data flow for the DGUID.
        Returns
        -------
        str
            The data flow associated with the DGUID.
        """
        return self.schema.data_flow

    def key(self, frequency: Frequency = Frequency.A5, stats_filter: Optional[StatsFilter] = None) -> str:  #TODO: use get_data.make_key
        # stats_filter = stats_filter or StatsFilter()
        return make_key(frequency=frequency, dguid=str(self), stats_filter=stats_filter)
        # return f'{frequency.name}.{self}' + (f'.{stats_filter}' if stats_filter else '')

    def __str__(self) -> str:
        return f'{self.vintage.value}{self.geocode.code}'
    
    async def get_data(
        self,
        frequency: Frequency = Frequency.A5,
        stats_filter: Optional[StatsFilter] = None,
        detail: Optional[Detail] = None,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Get data for the DGUID from the WDS API.

        Args:
            self (DGUID): The DGUID instance.
            frequency (Frequency, optional): The frequency of the data.
            stats_filter (StatsFilter, optional): The statistical filter to apply.

        Returns:
            Response: The API response containing the data.
        """
        resp = await get_sdmx_data(
            flow_ref=self.data_flow,
            dguid=f'{self}',
            frequency=frequency,
            stats_filter=stats_filter,
            format=Format.JSONDATA,
            detail=detail,
            timeout=timeout,
        )
        return resp.json()

    async def get_response(
        self,
        frequency: Frequency = Frequency.A5,
        stats_filter: Optional[StatsFilter] = None,
        detail: Optional[Detail] = None,
        timeout: Optional[float] = None,
    ) -> CensusDataResponse:
        """
        Get data as an enhanced CensusDataResponse object.

        Args:
            frequency (Frequency, optional): The frequency of the data.
            stats_filter (StatsFilter, optional): The statistical filter to apply.
            detail (Detail, optional): Level of detail for the response.
            timeout (float, optional): Request timeout in seconds.

        Returns:
            CensusDataResponse: Enhanced response object with dimension decoding and convenience methods.
        """
        raw_data = await self.get_data(frequency, stats_filter, detail, timeout)
        return CensusDataResponse(raw_data)

    async def get_dataframe(
        self,
        frequency: Frequency = Frequency.A5,
        stats_filter: Optional[StatsFilter] = None,
        detail: Optional[Detail] = None,
        timeout: Optional[float] = None,
    ) -> CensusDataFrame:
        """
        Get data as an enhanced CensusDataFrame.

        Args:
            frequency (Frequency, optional): The frequency of the data.
            stats_filter (StatsFilter, optional): The statistical filter to apply.
            detail (Detail, optional): Level of detail for the response.
            timeout (float, optional): Request timeout in seconds.

        Returns:
            CensusDataFrame: Enhanced DataFrame with census-specific methods.
        """
        response = await self.get_response(frequency, stats_filter, detail, timeout)
        df = response.to_dataframe()
        return CensusDataFrame(df)

    async def get_population_data(
        self,
        by_gender: bool = True,
        timeout: Optional[float] = None,
    ) -> CensusDataFrame:
        """
        Get population data for this geographic area.

        Args:
            by_gender (bool): Include gender breakdown.
            timeout (float, optional): Request timeout in seconds.

        Returns:
            CensusDataFrame: Population data with filtering methods.
        """
        df = await self.get_dataframe(timeout=timeout)
        return df.get_population_data()

    async def get_age_demographics(
        self,
        by_gender: bool = True,
        timeout: Optional[float] = None,
    ) -> CensusDataFrame:
        """
        Get age demographic data for this geographic area.

        Args:
            by_gender (bool): Include gender breakdown.
            timeout (float, optional): Request timeout in seconds.

        Returns:
            CensusDataFrame: Age demographic data.
        """
        df = await self.get_dataframe(timeout=timeout)
        return df.get_age_data()

    async def get_household_statistics(
        self,
        timeout: Optional[float] = None,
    ) -> CensusDataFrame:
        """
        Get household statistics for this geographic area.

        Args:
            timeout (float, optional): Request timeout in seconds.

        Returns:
            CensusDataFrame: Household statistics data.
        """
        df = await self.get_dataframe(timeout=timeout)
        return df.get_household_data()

    async def get_available_dimensions(
        self,
        timeout: Optional[float] = None,
    ) -> dict[str, Any]:
        """
        Discover what dimensions and values are available for this DGUID.

        Args:
            timeout (float, optional): Request timeout in seconds.

        Returns:
            dict: Available dimensions, characteristics, and values.
        """
        response = await self.get_response(timeout=timeout)
        return response.get_summary()

    async def describe_data(
        self,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Get a human-readable description of available data.

        Args:
            timeout (float, optional): Request timeout in seconds.

        Returns:
            str: Formatted description of available data.
        """
        summary = await self.get_available_dimensions(timeout)
        
        description = f"Data available for {self.geocode.name}:\n\n"
        description += f"Total series: {summary.get('total_series', 0)}\n"
        description += f"Dimensions: {', '.join(summary.get('dimensions', []))}\n\n"
        
        if 'available_values' in summary:
            description += "Sample characteristics:\n"
            for dim_name, values in summary['available_values'].items():
                description += f"  {dim_name}: {', '.join(values[:3])}...\n"
        
        return description

    @classmethod
    def from_str(cls, dguid_str: str) -> tuple[Optional[Frequency], Self, Optional[StatsFilter]]:
        """
        Create a DGUID instance from a string representation.

        Acceptable formats:
        - '2021PT01' (key:(vintage:geocode))
        - 'A5.2021PT01' (frequency.key:(vintage:geocode))
        - 'A5.2021PT01.{G}.{P}.{T}' (frequency.key:(vintage:geocode).stats_filter({gender}.{census_profile_characteristic}.{statistic_type}))
        - '2021PT01.{G}.{P}.{T}' (key:(vintage:geocode).stats_filter({gender}.{census_profile_characteristic}.{statistic_type}))

        
        Parameters
        ----------
        dguid_str : str
            The DGUID string to parse.
        
        Returns
        -------
        tuple[Self, StatsFilter]
            A tuple containing the DGUID instance and the associated StatsFilter.
        """
        parts = dguid_str.split('.')
        if len(parts) == 1:  # key only
            freq_str = None
            key_str = parts[0]
            filter_parts = None
        elif len(parts) == 2:  # frequency and key
            freq_str, key_str = parts
            filter_parts = None
        elif len(parts) == 4:  # key, and stats_filter
            key_str, *filter_parts = parts
            freq_str = None
        elif len(parts) == 5:  # frequency, key, and stats_filter
            freq_str, key_str, *filter_parts = parts
        else:  # Invalid format
            raise ValueError(f'Invalid DGUID format: {dguid_str}')

        frequency = Frequency[freq_str] if freq_str else None
        stats_filter = StatsFilter.from_parts(*filter_parts) if filter_parts else None

        vintage = Vintage(int(key_str[:4]))  # Extract vintage from the first 4 characters
        geocode_str = key_str[4:]
        geocode = get_geocode_from_str(geocode_str)

        
        return frequency, cls(
            geocode=geocode,
            vintage=vintage,
        ), stats_filter
