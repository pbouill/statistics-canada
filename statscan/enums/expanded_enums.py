"""
Template for expanding enhanced enums based on discovered SDMX dimension values.

This file provides a framework for systematically expanding the enum coverage
as new dimension values are discovered from actual API responses.
"""

from enum import Enum


class ExpandedGender(Enum):
    """Expanded gender enum with additional categories that may be found in data."""

    TOTAL_GENDER = 1
    MALE = 2
    FEMALE = 3
    # Add as discovered:
    # GENDER_DIVERSE = 4
    # NON_BINARY = 5

    @property
    def description(self) -> str:
        descriptions = {
            ExpandedGender.TOTAL_GENDER: "Total population, all genders",
            ExpandedGender.MALE: "Male population",
            ExpandedGender.FEMALE: "Female population",
        }
        return descriptions.get(self, "Unknown gender category")


class ExpandedCensusProfileCharacteristic(Enum):
    """
    Expanded census profile characteristics based on comprehensive 2021 Census Profile.

    This enum should be expanded as new characteristics are discovered in the data.
    The values below represent the most commonly used characteristics.
    """

    # Population and Demographics (1-99)
    POPULATION_COUNT = 1
    POPULATION_DENSITY_PER_KM2 = 2
    POPULATION_CHANGE_2016_TO_2021 = 3

    # Age Characteristics (100-199)
    TOTAL_AGE_GROUPS = 100
    AGE_0_TO_4 = 101
    AGE_5_TO_9 = 102
    AGE_10_TO_14 = 103
    AGE_15_TO_19 = 104
    AGE_20_TO_24 = 105
    AGE_25_TO_29 = 106
    AGE_30_TO_34 = 107
    AGE_35_TO_39 = 108
    AGE_40_TO_44 = 109
    AGE_45_TO_49 = 110
    AGE_50_TO_54 = 111
    AGE_55_TO_59 = 112
    AGE_60_TO_64 = 113
    AGE_65_TO_69 = 114
    AGE_70_TO_74 = 115
    AGE_75_TO_79 = 116
    AGE_80_TO_84 = 117
    AGE_85_AND_OVER = 118
    MEDIAN_AGE = 150
    AVERAGE_AGE = 151
    AGE_0_TO_14 = 160
    AGE_15_TO_64 = 161
    AGE_65_AND_OVER = 162

    # Household Characteristics (200-299)
    TOTAL_HOUSEHOLDS = 200
    AVERAGE_HOUSEHOLD_SIZE = 201
    ONE_PERSON_HOUSEHOLDS = 202
    TWO_PERSON_HOUSEHOLDS = 203
    THREE_PERSON_HOUSEHOLDS = 204
    FOUR_PERSON_HOUSEHOLDS = 205
    FIVE_OR_MORE_PERSON_HOUSEHOLDS = 206
    COUPLES_WITHOUT_CHILDREN = 210
    COUPLES_WITH_CHILDREN = 211
    LONE_PARENT_FAMILIES = 212

    # Dwelling Characteristics (300-399)
    TOTAL_DWELLINGS = 300
    OCCUPIED_DWELLINGS = 301
    UNOCCUPIED_DWELLINGS = 302
    DWELLINGS_OWNED = 310
    DWELLINGS_RENTED = 311
    DWELLINGS_BAND_HOUSING = 312

    # Housing Types (400-499)
    SINGLE_DETACHED_HOUSE = 400
    SEMI_DETACHED_HOUSE = 401
    ROW_HOUSE = 402
    APARTMENT_5_OR_MORE_STOREYS = 403
    APARTMENT_LESS_THAN_5_STOREYS = 404
    OTHER_SINGLE_ATTACHED = 405
    MOVABLE_DWELLING = 406

    # Marital Status (500-599)
    TOTAL_MARITAL_STATUS = 500
    MARRIED = 501
    LIVING_COMMON_LAW = 502
    NOT_MARRIED_NOT_LIVING_COMMON_LAW = 503
    NEVER_MARRIED = 504
    SEPARATED = 505
    DIVORCED = 506
    WIDOWED = 507

    # Language Characteristics (600-699)
    MOTHER_TONGUE_ENGLISH = 600
    MOTHER_TONGUE_FRENCH = 601
    MOTHER_TONGUE_NON_OFFICIAL = 602
    MOTHER_TONGUE_INDIGENOUS = 603
    KNOWLEDGE_OF_OFFICIAL_LANGUAGES_ENGLISH_ONLY = 610
    KNOWLEDGE_OF_OFFICIAL_LANGUAGES_FRENCH_ONLY = 611
    KNOWLEDGE_OF_OFFICIAL_LANGUAGES_BOTH = 612
    KNOWLEDGE_OF_OFFICIAL_LANGUAGES_NEITHER = 613

    # Immigration and Citizenship (700-799)
    TOTAL_IMMIGRANTS = 700
    RECENT_IMMIGRANTS_2016_2021 = 701
    NON_IMMIGRANTS = 702
    CANADIAN_CITIZENS = 703
    NOT_CANADIAN_CITIZENS = 704

    # Indigenous Identity (800-899)
    TOTAL_INDIGENOUS_IDENTITY = 800
    INDIGENOUS_IDENTITY = 801
    NON_INDIGENOUS_IDENTITY = 802
    FIRST_NATIONS = 803
    METIS = 804
    INUK_INUIT = 805

    # Visible Minority (900-999)
    TOTAL_VISIBLE_MINORITY = 900
    VISIBLE_MINORITY = 901
    NOT_VISIBLE_MINORITY = 902
    SOUTH_ASIAN = 903
    CHINESE = 904
    BLACK = 905
    FILIPINO = 906
    ARAB = 907
    LATIN_AMERICAN = 908
    SOUTHEAST_ASIAN = 909
    WEST_ASIAN = 910
    KOREAN = 911
    JAPANESE = 912

    # Education (1000-1099)
    NO_CERTIFICATE_DIPLOMA_DEGREE = 1000
    HIGH_SCHOOL_DIPLOMA = 1001
    POSTSECONDARY_CERTIFICATE_DIPLOMA_DEGREE = 1002
    APPRENTICESHIP_TRADES_CERTIFICATE = 1003
    COLLEGE_CEGEP_CERTIFICATE_DIPLOMA = 1004
    UNIVERSITY_CERTIFICATE_DIPLOMA_BELOW_BACHELOR = 1005
    BACHELOR_DEGREE = 1006
    UNIVERSITY_CERTIFICATE_DIPLOMA_ABOVE_BACHELOR = 1007
    DEGREE_IN_MEDICINE_DENTISTRY_VETERINARY_MEDICINE = 1008
    MASTER_DEGREE = 1009
    EARNED_DOCTORATE = 1010

    # Employment (1100-1199)
    LABOUR_FORCE_15_YEARS_AND_OVER = 1100
    EMPLOYMENT_RATE = 1101
    UNEMPLOYMENT_RATE = 1102
    PARTICIPATION_RATE = 1103

    # Income (1200-1299)
    MEDIAN_HOUSEHOLD_INCOME = 1200
    AVERAGE_HOUSEHOLD_INCOME = 1201
    MEDIAN_INDIVIDUAL_INCOME = 1202
    AVERAGE_INDIVIDUAL_INCOME = 1203
    LOW_INCOME_MEASURE_AFTER_TAX = 1204

    @property
    def description(self) -> str:
        """Get human-readable description of the characteristic."""
        # This would be a comprehensive mapping - showing just a few examples
        descriptions = {
            ExpandedCensusProfileCharacteristic.POPULATION_COUNT: "Total population count",
            ExpandedCensusProfileCharacteristic.POPULATION_DENSITY_PER_KM2: "Population density per square kilometer",
            ExpandedCensusProfileCharacteristic.MEDIAN_AGE: "Median age of population",
            ExpandedCensusProfileCharacteristic.TOTAL_HOUSEHOLDS: "Total number of households",
            ExpandedCensusProfileCharacteristic.AVERAGE_HOUSEHOLD_SIZE: "Average number of persons per household",
            ExpandedCensusProfileCharacteristic.TOTAL_DWELLINGS: "Total number of dwellings",
            ExpandedCensusProfileCharacteristic.MEDIAN_HOUSEHOLD_INCOME: "Median total household income",
        }
        return descriptions.get(self, f"Census characteristic {self.value}")

    @property
    def category(self) -> str:
        """Get the category this characteristic belongs to."""
        if self.value < 100:
            return "Population and Demographics"
        elif self.value < 200:
            return "Age Characteristics"
        elif self.value < 300:
            return "Households"
        elif self.value < 400:
            return "Dwellings"
        elif self.value < 500:
            return "Housing Types"
        elif self.value < 600:
            return "Marital Status"
        elif self.value < 700:
            return "Language"
        elif self.value < 800:
            return "Immigration and Citizenship"
        elif self.value < 900:
            return "Indigenous Identity"
        elif self.value < 1000:
            return "Visible Minority"
        elif self.value < 1100:
            return "Education"
        elif self.value < 1200:
            return "Employment"
        elif self.value < 1300:
            return "Income"
        else:
            return "Other"


class ExpandedStatisticType(Enum):
    """Expanded statistic types found in census data."""

    COUNT = 1  # Absolute count/number
    PERCENTAGE = 2  # Percentage of total
    RATE = 3  # Rate (e.g., per 1,000 or 100,000)
    MEDIAN = 4  # Median value
    AVERAGE = 5  # Mean/average value
    RATIO = 6  # Ratio between two values
    INDEX = 7  # Index value (e.g., relative to base year)
    DENSITY = 8  # Density measure (per square km, etc.)
    CHANGE = 9  # Change from previous period
    PERCENT_CHANGE = 10  # Percentage change

    @property
    def description(self) -> str:
        descriptions = {
            ExpandedStatisticType.COUNT: "Absolute count or number",
            ExpandedStatisticType.PERCENTAGE: "Percentage of total population/group",
            ExpandedStatisticType.RATE: "Rate per 1,000 or 100,000 population",
            ExpandedStatisticType.MEDIAN: "Median (middle) value",
            ExpandedStatisticType.AVERAGE: "Mean or average value",
            ExpandedStatisticType.RATIO: "Ratio between two values",
            ExpandedStatisticType.INDEX: "Index value relative to base",
            ExpandedStatisticType.DENSITY: "Density measure per area unit",
            ExpandedStatisticType.CHANGE: "Absolute change from previous period",
            ExpandedStatisticType.PERCENT_CHANGE: "Percentage change from previous period",
        }
        return descriptions.get(self, "Unknown statistic type")


class DimensionValueDiscovery:
    """Utility class to help discover and catalog new dimension values from API responses."""

    def __init__(self):
        self.discovered_values: dict[str, set[str]] = {}

    def analyze_response(self, response_data: dict) -> None:
        """Analyze an SDMX response to discover new dimension values."""
        if "data" not in response_data or "structures" not in response_data["data"]:
            return

        structures = response_data["data"]["structures"]
        if not structures:
            return

        structure = structures[0]
        if "dimensions" not in structure or "series" not in structure["dimensions"]:
            return

        series_dims = structure["dimensions"]["series"]

        for dim in series_dims:
            dim_name = dim.get("name", dim.get("id", "Unknown"))
            if dim_name not in self.discovered_values:
                self.discovered_values[dim_name] = set()

            values = dim.get("values", [])
            for value in values:
                value_name = value.get("name", value.get("id", "Unknown"))
                self.discovered_values[dim_name].add(value_name)

    def get_dimension_report(self) -> str:
        """Generate a report of discovered dimension values."""
        report = "Discovered Dimension Values:\n\n"

        for dim_name, values in self.discovered_values.items():
            report += f"{dim_name} ({len(values)} values):\n"
            sorted_values = sorted(list(values))
            for value in sorted_values[:10]:  # Show first 10
                report += f"  - {value}\n"
            if len(values) > 10:
                report += f"  ... and {len(values) - 10} more\n"
            report += "\n"

        return report

    def suggest_enum_additions(self, dimension_name: str) -> list[str]:
        """Suggest new enum values for a specific dimension."""
        if dimension_name not in self.discovered_values:
            return []

        values = list(self.discovered_values[dimension_name])

        # Generate enum-style names
        enum_suggestions = []
        for value in values:
            # Convert to enum-style name (uppercase, underscores)
            enum_name = value.upper().replace(" ", "_").replace("-", "_")
            enum_name = "".join(c for c in enum_name if c.isalnum() or c == "_")
            enum_suggestions.append(enum_name)

        return enum_suggestions


# Usage example for dimension discovery
async def discover_new_dimensions():
    """Example of how to discover new dimension values from API responses."""
    from statscan.dguid import DGUID
    from statscan.enums.auto.census_subdivision import CensusSubdivision

    # Create discovery utility
    discovery = DimensionValueDiscovery()

    # Get data from a few different areas
    dguids = [
        DGUID(geocode=CensusSubdivision.ONT_TORONTO),
        DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES),
        # Add more as needed
    ]

    for dguid in dguids:
        try:
            response_data = await dguid._get_census_data(timeout=15)
            discovery.analyze_response(response_data)
        except Exception as e:
            print(f"Error getting data for {dguid}: {e}")

    # Generate report
    report = discovery.get_dimension_report()
    print(report)

    # Get suggestions for specific dimensions
    gender_suggestions = discovery.suggest_enum_additions("Gender")
    print(f"Gender enum suggestions: {gender_suggestions}")

    char_suggestions = discovery.suggest_enum_additions("Census Profile Characteristic")
    print(f"Characteristic enum suggestions (first 10): {char_suggestions[:10]}")


if __name__ == "__main__":

    print("This is a template file for expanding enums.")
    print("Run discover_new_dimensions() to analyze actual API responses.")

    # Uncomment to run discovery:
    # asyncio.run(discover_new_dimensions())
