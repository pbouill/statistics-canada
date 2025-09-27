"""
Comprehensive statistics filter enums for Statistics Canada census data.

This module provides a unified filtering system with extensive enum coverage
for gender, census characteristics, and statistic types, along with convenience
factory methods for common filter combinations.
"""

from enum import Enum
from typing import Optional, Self, Any
from dataclasses import dataclass


class Gender(Enum):
    """Gender dimension values for census data."""

    TOTAL_GENDER = 1
    MALE = 2
    FEMALE = 3

    @property
    def description(self) -> str:
        descriptions = {
            Gender.TOTAL_GENDER: "Total population, all genders",
            Gender.MALE: "Male population",
            Gender.FEMALE: "Female population",
        }
        return descriptions.get(self, "Unknown gender category")


class CensusProfileCharacteristic(Enum):
    """Census profile characteristics - comprehensive list based on 2021 Census."""

    # Population counts
    POPULATION_COUNT = 1
    POPULATION_DENSITY_PER_KM2 = 2

    # Age characteristics
    TOTAL_AGE_GROUPS = 3
    AGE_0_TO_14 = 4
    AGE_15_TO_64 = 5
    AGE_65_AND_OVER = 6
    MEDIAN_AGE = 7
    AVERAGE_AGE = 8

    # Household characteristics
    TOTAL_HOUSEHOLDS = 100
    AVERAGE_HOUSEHOLD_SIZE = 101
    ONE_PERSON_HOUSEHOLDS = 102
    MULTIPLE_PERSON_HOUSEHOLDS = 103

    # Dwelling characteristics
    TOTAL_DWELLINGS = 200
    OCCUPIED_DWELLINGS = 201
    UNOCCUPIED_DWELLINGS = 202

    # Housing types
    SINGLE_DETACHED_HOUSE = 300
    APARTMENT_BUILDING = 301
    ROW_HOUSE = 302
    MOBILE_HOME = 303

    # Language characteristics
    MOTHER_TONGUE_ENGLISH = 400
    MOTHER_TONGUE_FRENCH = 401
    MOTHER_TONGUE_NON_OFFICIAL = 402

    # Immigration and citizenship
    TOTAL_IMMIGRANTS = 500
    RECENT_IMMIGRANTS = 501
    NON_IMMIGRANTS = 502
    CANADIAN_CITIZENS = 503

    # Education
    NO_CERTIFICATE_DIPLOMA_DEGREE = 600
    HIGH_SCHOOL_DIPLOMA = 601
    TRADES_CERTIFICATE = 602
    COLLEGE_DIPLOMA = 603
    UNIVERSITY_DEGREE = 604

    # Employment
    LABOUR_FORCE_PARTICIPATION_RATE = 700
    EMPLOYMENT_RATE = 701
    UNEMPLOYMENT_RATE = 702

    # Income
    MEDIAN_HOUSEHOLD_INCOME = 800
    AVERAGE_HOUSEHOLD_INCOME = 801
    MEDIAN_INDIVIDUAL_INCOME = 802
    LOW_INCOME_PREVALENCE = 803

    @property
    def description(self) -> str:
        """Get human-readable description of the characteristic."""
        descriptions = {
            CensusProfileCharacteristic.POPULATION_COUNT: "Total population count",
            CensusProfileCharacteristic.POPULATION_DENSITY_PER_KM2: "Population density per square kilometer",
            CensusProfileCharacteristic.MEDIAN_AGE: "Median age of population",
            CensusProfileCharacteristic.TOTAL_HOUSEHOLDS: "Total number of households",
            CensusProfileCharacteristic.AVERAGE_HOUSEHOLD_SIZE: "Average number of persons per household",
            CensusProfileCharacteristic.TOTAL_DWELLINGS: "Total number of dwellings",
            CensusProfileCharacteristic.MEDIAN_HOUSEHOLD_INCOME: "Median total household income",
            # Add more as needed
        }
        return descriptions.get(self, f"Census characteristic {self.value}")

    @property
    def category(self) -> str:
        """Get the category this characteristic belongs to."""
        if self.value < 100:
            return "Population and Age"
        elif self.value < 200:
            return "Households"
        elif self.value < 300:
            return "Dwellings"
        elif self.value < 400:
            return "Housing Types"
        elif self.value < 500:
            return "Language"
        elif self.value < 600:
            return "Immigration and Citizenship"
        elif self.value < 700:
            return "Education"
        elif self.value < 800:
            return "Employment"
        elif self.value < 900:
            return "Income"
        else:
            return "Other"


class StatisticType(Enum):
    """Types of statistics available for census characteristics."""

    COUNT = 1  # Absolute count/number
    PERCENTAGE = 2  # Percentage of total
    RATE = 3  # Rate (e.g., per 1,000 or 100,000)
    MEDIAN = 4  # Median value
    AVERAGE = 5  # Mean/average value
    RATIO = 6  # Ratio between two values
    INDEX = 7  # Index value (e.g., relative to base year)

    @property
    def description(self) -> str:
        descriptions = {
            StatisticType.COUNT: "Absolute count or number",
            StatisticType.PERCENTAGE: "Percentage of total population/group",
            StatisticType.RATE: "Rate per 1,000 or 100,000 population",
            StatisticType.MEDIAN: "Median (middle) value",
            StatisticType.AVERAGE: "Mean or average value",
            StatisticType.RATIO: "Ratio between two values",
            StatisticType.INDEX: "Index value relative to base",
        }
        return descriptions.get(self, "Unknown statistic type")


@dataclass
class StatsFilter:
    """Comprehensive statistics filter with dimension support."""

    gender: Optional[Gender] = None
    census_profile_characteristic: Optional[CensusProfileCharacteristic] = None
    statistic_type: Optional[StatisticType] = None

    def __str__(self) -> str:
        """Get a string representation of the StatsFilter."""
        return (
            f"{self.gender.value if self.gender else ''}."
            f"{self.census_profile_characteristic.value if self.census_profile_characteristic else ''}."
            f"{self.statistic_type.value if self.statistic_type else ''}"
        )

    @classmethod
    def from_str(cls, filter_str: str) -> Self:
        """Create a StatsFilter instance from a string representation."""
        return cls.from_parts(*filter_str.split("."))

    @classmethod
    def from_parts(cls, gender_str: str, cpc_str: str, stattype_str: str) -> Self:
        """Create a StatsFilter instance from individual parts."""
        return cls(
            gender=Gender(int(gender_str)) if gender_str else None,
            census_profile_characteristic=CensusProfileCharacteristic(int(cpc_str))
            if cpc_str
            else None,
            statistic_type=StatisticType(int(stattype_str)) if stattype_str else None,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "gender": {
                "value": self.gender.value if self.gender else None,
                "name": self.gender.name if self.gender else None,
                "description": self.gender.description if self.gender else None,
            },
            "characteristic": {
                "value": self.census_profile_characteristic.value
                if self.census_profile_characteristic
                else None,
                "name": self.census_profile_characteristic.name
                if self.census_profile_characteristic
                else None,
                "description": self.census_profile_characteristic.description
                if self.census_profile_characteristic
                else None,
                "category": self.census_profile_characteristic.category
                if self.census_profile_characteristic
                else None,
            },
            "statistic_type": {
                "value": self.statistic_type.value if self.statistic_type else None,
                "name": self.statistic_type.name if self.statistic_type else None,
                "description": self.statistic_type.description
                if self.statistic_type
                else None,
            },
        }


# Convenience factory functions for common filters
class CommonFilters:
    """Factory class for commonly used filter combinations."""

    @staticmethod
    def population_total() -> StatsFilter:
        """Total population count for all genders."""
        return StatsFilter(
            gender=Gender.TOTAL_GENDER,
            census_profile_characteristic=CensusProfileCharacteristic.POPULATION_COUNT,
            statistic_type=StatisticType.COUNT,
        )

    @staticmethod
    def population_by_gender(gender: Gender) -> StatsFilter:
        """Population count by specific gender."""
        return StatsFilter(
            gender=gender,
            census_profile_characteristic=CensusProfileCharacteristic.POPULATION_COUNT,
            statistic_type=StatisticType.COUNT,
        )

    @staticmethod
    def median_age_total() -> StatsFilter:
        """Median age for total population."""
        return StatsFilter(
            gender=Gender.TOTAL_GENDER,
            census_profile_characteristic=CensusProfileCharacteristic.MEDIAN_AGE,
            statistic_type=StatisticType.MEDIAN,
        )

    @staticmethod
    def household_income_median() -> StatsFilter:
        """Median household income."""
        return StatsFilter(
            gender=Gender.TOTAL_GENDER,
            census_profile_characteristic=CensusProfileCharacteristic.MEDIAN_HOUSEHOLD_INCOME,
            statistic_type=StatisticType.MEDIAN,
        )

    @staticmethod
    def total_dwellings() -> StatsFilter:
        """Total dwelling count."""
        return StatsFilter(
            gender=Gender.TOTAL_GENDER,
            census_profile_characteristic=CensusProfileCharacteristic.TOTAL_DWELLINGS,
            statistic_type=StatisticType.COUNT,
        )
