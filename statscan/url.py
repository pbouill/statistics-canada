"""Constants for Statistics Canada API endpoints.

This module defines base URLs for various Statistics Canada data services including
the Web Data Service (WDS), Census SDMX API, and geographic attribute files.
"""

WDS_URL = "https://www150.statcan.gc.ca/t1/wds/rest"
CENSUS_SDMX_BASE_URL = (
    "https://api.statcan.gc.ca/census-recensement/profile/sdmx/rest"
)
GEO_ATTR_FILE_2021_URL = (
    "https://www12.statcan.gc.ca/census-recensement/2021/geo/aip-pia/"
    "attribute-attribs/files-fichiers/2021_92-151_X.zip"
)
