"""WDS API response status code enumeration."""

from enum import Enum


class WDSResponseStatus(Enum):
    """Status codes returned by the WDS API."""

    SUCCESS = 0  # (Success) {'codeTextFr': 'Succès'}
    INVALID_DATE = 1  # (Invalid date) {'codeTextFr': 'Date invalide'}
    # (Invalid cube and series combination)  # noqa: E501
    INVALID_CUBE_AND_SERIES_COMBINATION = 2
    REQUEST_FAILED = 3  # (Request failed) {'codeTextFr': 'La demande a échouée'}
    VECTOR_IS_INVALID = 4  # (Vector is invalid) {'codeTextFr': 'Vecteur invalide'}
    # (Cube product id is invalid)  # noqa: E501
    CUBE_PRODUCT_ID_IS_INVALID = 5
    # (Cube is currently being published. Please try again later.)  # noqa: E501
    CUBE_IS_CURRENTLY_BEING_PUBLISHED_PLEASE_TRY_AGAIN_LATER = 6
    # (Cube is not available. Contact: 1-800-263-1136)  # noqa: E501
    CUBE_IS_NOT_AVAILABLE = 7
    # (Invalid number of reference periods)  # noqa: E501
    INVALID_NUMBER_OF_REFERENCE_PERIODS = 8
