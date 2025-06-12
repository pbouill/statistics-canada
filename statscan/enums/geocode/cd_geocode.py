from statscan.enums.geocode.pr_geocode import ProvinceGeoCode
from statscan.enums.auto import ProvinceTerritory, CensusDivision


class CensusDivisionGeoCode(ProvinceGeoCode):
    """
    CensusDivisionGeoCode is a subclass of ProvinceGeoCode that represents
    the geographic code for a census division within a province or territory.
    It inherits properties and methods from ProvinceGeoCode, allowing it to
    access province-level information while also providing specific details
    related to census divisions.
    """
    
    @property
    def cduid(self) -> str:
        """
        Get the Census Division Unique Identifier (CDUID).

        Returns
        -------
        str
            The unique identifier for the census division.
        """
        start = ProvinceTerritory.get_nchars()
        end = start + CensusDivision.get_nchars()
        return self.uid[start:end]

    @property
    def census_division(self) -> CensusDivision:
        """
        Get the CensusDivision enum instance associated with this code.

        Returns
        -------
        CensusDivision
            The census division associated with this geographic code.
        """
        return CensusDivision(int(self.cduid))
