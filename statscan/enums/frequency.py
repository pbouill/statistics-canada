"""Frequency enumeration for StatsCan data collection intervals."""

from enum import Enum


class Frequency(Enum):
    """Data collection frequency intervals."""

    A5 = 5  # Every 5 years
