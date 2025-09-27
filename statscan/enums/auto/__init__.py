import logging

from statscan.enums.geocode.geocode import GeoCode
from statscan.util.pkg import get_subpkg_subcls


logger = logging.getLogger(name=__name__)


try:
    from .province_territory import ProvinceTerritory  # noqa
except ImportError as e:
    logger.error(
        f"Failed to import ProvinceTerritory enum: {e}. Will create a placeholder class."
    )

    class ProvinceTerritory(GeoCode):  # type: ignore[no-redef]
        """
        Placeholder class for ProvinceTerritory enum.
        """

        pass


try:
    from .census_division import CensusDivision  # noqa
except ImportError as e:
    logger.error(
        f"Failed to import CensusDivision enum: {e}. Will create a placeholder class."
    )

    class CensusDivision(GeoCode):  # type: ignore[no-redef]
        """
        Placeholder class for CensusDivision enum.
        """

        pass


try:
    from .census_metropolitan_area import CensusMetropolitanArea
except ImportError as e:
    logger.error(
        f"Failed to import CensusMetropolitanArea enum: {e}. Will create a placeholder class."
    )

    class CensusMetropolitanArea(GeoCode):  # type: ignore[no-redef]
        """
        Placeholder class for CensusMetropolitanArea enum.
        """

        pass


__all__ = [
    "GeoCode",
    "ProvinceTerritory",
    "CensusDivision",
    "CensusMetropolitanArea",
]

ALL_GEOCODES: dict[str, type[GeoCode]] = get_subpkg_subcls(cls=GeoCode)


def get_geocode_from_str(geocode: str) -> GeoCode:
    """
    Get a GeoCode enum instance from a string.

    Args:
        geocode (str): The string representation of the geocode.

    Returns:
        GeoCode: The corresponding GeoCode enum instance.

    Raises:
        ValueError: If the geocode string does not match any known geocode.
    """
    for gcls in ALL_GEOCODES.values():
        if geocode.startswith(gcls.get_schema().value):
            uid = geocode[len(gcls.get_schema().value) :]
            return gcls.from_uid(uid)
    raise ValueError(f"Unknown geocode: {geocode}")
