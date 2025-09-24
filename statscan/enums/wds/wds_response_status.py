from enum import Enum


class WDSResponseStatus(Enum):
    SUCCESS = 0  # (Success) {'codeTextFr': 'Succès'}
    INVALID_DATE = 1  # (Invalid date) {'codeTextFr': 'Date invalide'}
    INVALID_CUBE_AND_SERIES_COMBINATION = 2  # (Invalid cube and series combination) {'codeTextFr': 'Combinaison invalide de cube et de série'}
    REQUEST_FAILED = 3  # (Request failed) {'codeTextFr': 'La demande a échouée'}
    VECTOR_IS_INVALID = 4  # (Vector is invalid) {'codeTextFr': 'Vecteur invalide'}
    CUBE_PRODUCT_ID_IS_INVALID = 5  # (Cube product id is invalid) {'codeTextFr': 'Identificateur du produit invalide'}
    CUBE_IS_CURRENTLY_BEING_PUBLISHED_PLEASE_TRY_AGAIN_LATER = 6  # (Cube is currently being published. Please try again later.) {'codeTextFr': 'Le cube est en cours de publication. Veuillez réessayer plus tard.'}
    CUBE_IS_NOT_AVAILABLE = 7  # (Cube is not available. For more information, contact us (toll-free 1-800-263-1136;   514-283-8300; STATCAN.infostats-infostats.STATCAN@canada.ca).) {'codeTextFr': "Le cube n'est pas disponible. Pour plus d'information, contactez-nous\nsans frais 1-800-263-1136; 514-283-8300;   STATCAN.infostats-infostats.STATCAN@canada.ca)."}
    INVALID_NUMBER_OF_REFERENCE_PERIODS = 8  # (Invalid number of reference periods) {'codeTextFr': 'Nombre de périodes de référence invalide.'}
