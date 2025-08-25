from enum import Enum


class Status(Enum):
    NORMAL = 0  # (normal) {'statusRepresentationEn': None, 'statusRepresentationFr': None, 'statusDescFr': 'normal'}
    NOT_AVAILABLE_FOR_A_SPECIFIC_REFERENCE_PERIOD = 1  # (not available for a specific reference period) {'statusRepresentationEn': '..', 'statusRepresentationFr': '..', 'statusDescFr': 'indisponible pour une période de référence précise'}
    LESS_THAN_THE_LIMIT_OF_DETECTION = 10  # (less than the limit of detection) {'statusRepresentationEn': '<LOD', 'statusRepresentationFr': '<LDD', 'statusDescFr': 'inférieur à la limite de détection'}
    VALUE_ROUNDED_TO_ZERO = 2  # (value rounded to 0 (zero) where there is a meaningful distinction between true zero and the value that was rounded) {'statusRepresentationEn': '0s', 'statusRepresentationFr': '0s', 'statusDescFr': 'valeur arrondie à 0 (zéro) là où il y a une distinction importante entre le zéro absolu et la valeur arrondie'}
    DATA_QUALITY_EXCELLENT = 3  # (data quality: excellent) {'statusRepresentationEn': 'A', 'statusRepresentationFr': 'A', 'statusDescFr': 'qualité des données : excellente'}
    DATA_QUALITY_VERY_GOOD = 4  # (data quality: very good) {'statusRepresentationEn': 'B', 'statusRepresentationFr': 'B', 'statusDescFr': 'qualité des données : très bonne'}
    DATA_QUALITY_GOOD = 5  # (data quality: good) {'statusRepresentationEn': 'C', 'statusRepresentationFr': 'C', 'statusDescFr': 'qualité des données : bonne'}
    DATA_QUALITY_ACCEPTABLE = 6  # (data quality: acceptable) {'statusRepresentationEn': 'D', 'statusRepresentationFr': 'D', 'statusDescFr': 'qualité des données : acceptable'}
    USE_WITH_CAUTION = 7  # (use with caution) {'statusRepresentationEn': 'E', 'statusRepresentationFr': 'E', 'statusDescFr': 'à utiliser avec prudence'}
    TOO_UNRELIABLE_TO_BE_PUBLISHED = 8  # (too unreliable to be published) {'statusRepresentationEn': 'F', 'statusRepresentationFr': 'F', 'statusDescFr': 'trop peu fiable pour être publié'}
    NOT_APPLICABLE = 9  # (not applicable) {'statusRepresentationEn': '...', 'statusRepresentationFr': '...', 'statusDescFr': "n'ayant pas lieu de figurer"}
