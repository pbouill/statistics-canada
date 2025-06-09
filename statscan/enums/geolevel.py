from typing import Self
from enum import StrEnum


class GeoLevel(StrEnum):
    """
    Enum for GeoLevel values used in StatsCan DGUID.
    see: https://www12.statcan.gc.ca/census-recensement/2021/ref/dict/az/definition-eng.cfm
    """
    CAN = 'A0000'  # Canada
    PR = 'A0002'  # Province or Territory
    CD = 'A0003'  # Census Division
    FED = 'A0004'  # Federal Electoral District
    CSD = 'A0005'  # Census Subdivision
    DPL = 'A0006'  # Designated Place
    HR = 'A0007'  # Health Region
    HR_NEW = 'S0504'  # Health Region (new)
    FSA = 'A0011'  # Forward Sortation Area
    ER = 'S0500'  # Economic Region
    CMA = 'S0503'  # Census Metropolitan Area
    CA = 'S0504'  # Census Agglomeration
    CT = 'S0507'  # Census Tract
    POPCTR = 'S0510'  # Population Centre
    DA = 'S0512'  # Dissemination Area
    ADA = 'S0516'  # Aggregated Dissemination Area

    @classmethod
    def from_dguid(cls, dguid: str) -> Self:
        """
        Get the GeoLevel enum from a DGUID string.
        {Year:4}{GeoLevel:5}{ProvinceTerritory:2}{UniqueIdentifier:}

        Parameters
        ----------
        dguid: str
            The DGUID string to parse.

        Returns
        -------
        GeoLevel
            The corresponding GeoLevel enum value.
        """
        return cls(dguid[4:9])
    
    @property
    def is_administrative_area(self) -> bool:
        """
        Check if the GeoLevel is an administrative area.

        Returns
        -------
        bool
            True if the GeoLevel is an administrative area, False otherwise.
        """
        return self.value.startswith('A')
    
    @property
    def is_statistical_area(self) -> bool:
        """
        Check if the GeoLevel is a statistical area.

        Returns
        -------
        bool
            True if the GeoLevel is a statistical area, False otherwise.
        """
        return self.value.startswith('S')
    
    @property
    def is_combined_area(self) -> bool:
        """
        Check if the GeoLevel is a combined area.

        Returns
        -------
        bool
            True if the GeoLevel is a combined area, False otherwise.
        """
        return self.value.startswith('C')
    
    @property
    def is_blended_area(self) -> bool:
        """
        Check if the GeoLevel is a blended area.

        Returns
        -------
        bool
            True if the GeoLevel is a blended area, False otherwise.
        """
        return self.value.startswith('B')

    @property
    def data_flow(self) -> str:
        """
        Get the data flow for the GeoLevel.

        Returns
        -------
        str
            The data flow for the GeoLevel.
        """
        return f'DF_{self.name.upper()}'