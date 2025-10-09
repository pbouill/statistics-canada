"""SDMX dimension models for data structure organization."""

from ...base import Base
from .dimension.observation import Observation
from .dimension.series import Series


class Dimensions(Base):
    """Represents the dimensions of a data structure in SDMX."""

    dataSet: list = []  # noqa: N815
    series: list[Series] = []
    observation: list[Observation] = []

    @property
    def series_names(self) -> list[str]:
        """Returns a list of series names."""
        return [s.name for s in self.series]

    @property
    def series_ids(self) -> list[str]:
        """Returns a list of series IDs."""
        return [s.id for s in self.series]

    @property
    def observation_names(self) -> list[str]:
        """Returns a list of observation names."""
        return [o.name for o in self.observation]

    @property
    def observation_ids(self) -> list[str]:
        """Returns a list of observation IDs."""
        return [o.id for o in self.observation]

    def __getitem__(self, key: str) -> Series:
        """Get a series by its ID."""
        for series in self.series:
            if series.id == key:
                return series
        raise KeyError(f"Series with ID '{key}' not found.")

    def get_series_by_key_position(self, key_position: int) -> Series | None:
        """Get a series by its key position."""
        matches = [s for s in self.series if s.keyPosition == key_position]
        if len(matches) == 0:
            return None
        elif len(matches) > 1:
            series_ids = ", ".join(s.id for s in matches)
            raise ValueError(
                f"Multiple series found with key position '{key_position}': "
                f"{series_ids}"
            )
        return matches[0]

    def get_series_by_name(self, name: str, language: str = "en") -> Series | None:
        """Get a series by its name or display name."""
        for series in self.series:
            if series.name == name or series.get_display_name(language) == name:
                return series
        return None

    def get_observation_by_name(
        self, name: str, language: str = "en"
    ) -> Observation | None:
        """Get an observation by its name or display name."""
        for obs in self.observation:
            if obs.name == name or obs.get_display_name(language) == name:
                return obs
        return None

    @property
    def summary(self) -> dict:
        """Get a summary of dimensions."""
        return {
            "series_count": len(self.series),
            "observation_count": len(self.observation),
            "dataset_count": len(self.dataSet),
            "series_ids": self.series_ids,
            "observation_ids": self.observation_ids,
        }
