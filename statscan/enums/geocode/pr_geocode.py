
from statscan.enums.geocode.geocode import GeoCode
from statscan.enums.auto import ProvinceTerritory


class ProvinceGeoCode(GeoCode):
    """
    ProvinceGeoCode is a subclass of GeoCode that represents the geographic code
    for a province or territory in Canada. It provides properties to access
    the unique identifier for the province or territory and the associated
    ProvinceTerritory enum instance.
    """

    @property
    def pruid(self) -> str:
        """
        Get the Province or Territory Unique Identifier (PRUID).
        Returns
        -------
        str
            The unique identifier for the province or territory.
        """
        return self.uid[:ProvinceTerritory.get_nchars()]

    @property
    def province_territory(self) -> ProvinceTerritory:
        """
        Get the Province or Territory enum instance associated with this code.
        Returns
        -------
        ProvinceTerritory
            The enum instance for the province or territory.
        """
        return ProvinceTerritory(int(self.pruid))


