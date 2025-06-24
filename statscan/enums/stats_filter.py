from enum import Enum
from typing import Optional, Self
from dataclasses import dataclass


class Gender(Enum):
    TOTAL_GENDER = 1


class CensusProfileCharacteristic(Enum):
    POPULATION_COUNT = 1


class StatisticType(Enum):
    COUNT = 1


@dataclass
class StatsFilter:
    gender: Optional[Gender] = None
    census_profile_characteristic: Optional[CensusProfileCharacteristic] = None
    statistic_type: Optional[StatisticType] = None

    def __str__(self) -> str:
        """
        Get a string representation of the StatsFilter.
        
        Returns
        -------
        str
            A string representation of the StatsFilter.
        """
        return f'{self.gender.value if self.gender else ""}.' \
            f'{self.census_profile_characteristic.value if self.census_profile_characteristic else ""}.' \
            f'{self.statistic_type.value if self.statistic_type else ""}'
    
    @classmethod
    def from_str(cls, filter_str: str) -> Self:
        """
        Create a StatsFilter instance from a string representation.
        
        Parameters
        ----------
        filter_str : str
            The string representation of the StatsFilter.
        
        Returns
        -------
        StatsFilter
            An instance of StatsFilter created from the string.
        """
        return cls.from_parts(*filter_str.split('.'))
        
    
    @classmethod
    def from_parts(cls, gender_str: str, cpc_str: str, stattype_str: str) -> Self:
        """
        Create a StatsFilter instance from individual parts.
        
        Parameters
        ----------
        gender_str : str
            The string representation of the gender.
        cpc_str : str
            The string representation of the census profile characteristic.
        stattype_str : str
            The string representation of the statistic type.

        Returns
        -------
        StatsFilter
            An instance of StatsFilter created from the individual parts.
        """
        return cls(
            gender=Gender(int(gender_str)) if gender_str else None,
            census_profile_characteristic=CensusProfileCharacteristic(int(cpc_str)) if cpc_str else None,
            statistic_type=StatisticType(int(stattype_str)) if stattype_str else None
        )
