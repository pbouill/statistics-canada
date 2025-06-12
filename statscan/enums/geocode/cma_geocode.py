from statscan.enums.geocode.geocode import FloatGeoCode
from statscan.enums.auto import CensusMetropolitanArea, ProvinceTerritory


class CensusMetropolitanAreaGeoCode(FloatGeoCode):
    """
    Enum for Census Metropolitan Areas (CMAs) in Canada.
    """
    
    @property
    def cmauid(self) -> str:
        """
        Get the Census Metropolitan Area Unique Identifier (CMAUID).

        Returns
        -------
        str
            The unique identifier for the census metropolitan area.
        """
        return self.uid[:3]
    
    @property
    def census_metropolitan_area(self) -> CensusMetropolitanArea:
        """
        Get the Census Metropolitan Area enum instance.

        Returns
        -------
        CensusMetropolitanArea
            The enum instance for the census metropolitan area.
        """
        for cma in CensusMetropolitanArea:
            if cma.uid == self.cmauid:
                return cma
        raise ValueError(f"Census Metropolitan Area with UID {self.cmauid} not found.")
    
    @property
    def province_territory(self) -> ProvinceTerritory:
        """
        Get the Province or Territory associated with this Census Metropolitan Area.

        Returns
        -------
        ProvinceTerritory
            The enum instance for the province or territory.
        """
        return self.census_metropolitan_area.province_territory