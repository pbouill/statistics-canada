from typing import Optional
from dataclasses import dataclass
from enum import Enum

from statscan.enums.schema import Schema
from statscan.enums.vintage import Vintage
from statscan.enums.frequency import Frequency
from statscan.enums.geocode.geocode import GeoCode


class Gender(Enum):
    TOTAL_GENDER = 1


class CensusProfileCharacteristic(Enum):
    POPULATION_COUNT = 1


class StatisticType(Enum):
    COUNT = 1


@dataclass
class DGUID:
    '''
    Data Geographic Unique Identifier (DGUID) for StatsCan datasets.
    see: https://www12.statcan.gc.ca/wds-sdw/2021profile-profil2021-eng.cfm
    '''
    geocode: GeoCode
    vintage: Vintage = Vintage.CENSUS_2021  # Default vintage is Census 2021
    frequency: Frequency = Frequency.A5  # Default frequency is every 5 years

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
    
    @property
    def key(self) -> str:
        return f'{self.frequency.name}.{self.vintage}.{self.geocode.code}'

    
    def get_dguid(
        self, 
        gender: Optional[Gender] = None, 
        census_profile_characteristic: Optional[CensusProfileCharacteristic] = None, 
        statistic_type: Optional[StatisticType] = None
    ) -> str:
        """
        Generate the DGUID string based on the provided parameters.
        Parameters
        ----------
        gender: Optional[Gender]
            The gender to include in the DGUID.
        census_profile_characteristic: Optional[CensusProfileCharacteristic]
            The census profile characteristic to include in the DGUID.
        statistic_type: Optional[StatisticType]
            The statistic type to include in the DGUID.

        Returns
        -------
        str
            The generated DGUID string.
        """
        return f'{self.key}.{gender or ""}.{census_profile_characteristic or ""}.{statistic_type or ""}'
