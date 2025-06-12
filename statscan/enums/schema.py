from __future__ import annotations
from typing import Self
from enum import StrEnum, Enum

class Schema(StrEnum):
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
    FSA = 'A0011'  # Forward Sortation Area
    ER = 'S0500'  # Economic Region
    CCS = 'S0502'  # Census Consolidated Subdivision
    CMA = 'S0503'  # [CMADGUID] Census Metropolitan Area
    CA = 'S0504'  # [CMADGUID] Census Agglomeration
    CT = 'S0507'  # Census Tract
    MIZ = 'S0509'  # [CMADGUID] Metropolitan Influenced Zone
    OUTSIDE_CA = 'S0517'  # [CMADGUID] Census Subdivision in a Territory outside a Census Agglomeration


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
        if self in (Schema.CMA, Schema.CA, Schema.MIZ, Schema.OUTSIDE_CA):
            return 'DF_CMACA'
        return f'DF_{self.name.upper()}'
    

class SACType(Enum):
    """
    see: https://www12.statcan.gc.ca/census-recensement/2021/geo/ref/domain-domaine/index2021-eng.cfm?lang=e&id=SACtype&getgeo=Continue
    """
    CMA = 1  # Census Subdivision within a Census Metropolitan Area
    CA_WITH_CT = 2  # Census Subdivision within a Census Agglomeration with Census Tract
    CA = 3  # Census Subdivision within a Census Agglomeration without Census Tract
    MIZ_STRONG = 4  # Census Subdivision in a Strong Metropolitan Influenced Zone (MIZ)
    MIZ_MODERATE = 5  # Census Subdivision in a Moderate Metropolitan Influenced Zone (MIZ)
    MIZ_WEAK = 6  # Census Subdivision in a Weak Metropolitan Influenced Zone (MIZ)
    MIZ_NONE = 7  # Census Subdivision in a Non-Metropolitan Influenced Zone (MIZ)
    TERRITORY_OUTSIDE_CA = 8  # Census Subdivision in a Territory outside a Census Agglomeration





