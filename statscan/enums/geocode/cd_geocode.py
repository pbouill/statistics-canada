"""Census division geographic code enumeration."""

from statscan.enums.auto import CensusDivision, ProvinceTerritory
from statscan.enums.geocode.pr_geocode import ProvinceGeoCode


class CensusDivisionGeoCode(ProvinceGeoCode):
    """Geographic code for a census division within a province or territory.

    Subclass of ProvinceGeoCode that inherits province-level properties and
    methods while also providing specific details related to census divisions.

    """

    @property
    def cduid(self) -> str:
        """Get the Census Division Unique Identifier (CDUID).

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
        """Get the CensusDivision enum instance associated with this code.

        Returns
        -------
        CensusDivision
            The census division associated with this geographic code.

        """
        return CensusDivision(int(self.cduid))
