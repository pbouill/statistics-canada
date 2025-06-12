import logging

from statscan.enums.geocode.geocode import GeoCode

logger = logging.getLogger(name=__name__)


try:
    from .province_territory import ProvinceTerritory
except ImportError as e:
    logger.error(f'Failed to import ProvinceTerritory enum: {e}. Will create a placeholder class.')
    class ProvinceTerritory(GeoCode):  # type: ignore[no-redef]
        """
        Placeholder class for ProvinceTerritory enum.
        """
        pass

try:
    from .census_division import CensusDivision
except ImportError as e:
    logger.error(f'Failed to import CensusDivision enum: {e}. Will create a placeholder class.')
    class CensusDivision(GeoCode):  # type: ignore[no-redef]
        """
        Placeholder class for CensusDivision enum.
        """
        pass

try:
    from .census_metropolitan_area import CensusMetropolitanArea
except ImportError as e:
    logger.error(f'Failed to import CensusMetropolitanArea enum: {e}. Will create a placeholder class.')
    class CensusMetropolitanArea(GeoCode):  # type: ignore[no-redef]
        """
        Placeholder class for CensusMetropolitanArea enum.
        """
        pass