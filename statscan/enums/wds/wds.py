from typing import Optional
from enum import StrEnum, auto


class WDSParam(StrEnum):
    def add_to_params(self, params: Optional[dict[str, str]]) -> dict[str, str]:
        """
        Add the detail level to the provided parameters dictionary.

        Args:
            params (dict[str, str]): The parameters dictionary to update.
        """
        params = params or {}
        params[self.__class__.__name__.lower()] = self.value
        return params


class Detail(WDSParam):
    FULL = auto()
    DATA_ONLY = auto()
    SERIESKEYSONLY = auto()
    NODATA = auto()


class Format(WDSParam):
    CSV = auto()
    JSONDATA = auto()


class WDSDATAMIME(StrEnum):
    SDMX_ML = "application/vnd.sdmx.genericdata+xml;version=2.1"
    SDMX_ML_2_1 = "application/vnd.sdmx.structurespecificdata+xml;version=2.1"
    SDMX_JSON = "application/vnd.sdmx.data+json;version=1.0.0-wd"
    CSV = "text/csv"


class WDSMETADATAMIME(StrEnum):
    SDMX_ML = "application/vnd.sdmx.structure+xml;version=2.1"
    SDMX_JSON = "application/vnd.sdmx.structure+json;version=1.0"
