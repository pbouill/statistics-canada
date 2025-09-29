from typing import Optional, Any

from pydantic import field_validator

from ...base import Base


class Series(Base):
    """
    Represents a data series in an SDMX dataset.
    Based on actual structure: {attributes (list), annotations (list), observations (dict)}
    """

    attributes: list[Optional[int]] = []
    annotations: list[int] = []
    observations: dict[int, list[Optional[float | int]]] = {}

    @field_validator("observations", mode="before")
    @classmethod
    def validate_observations(cls, observations: dict[int, list[Any]]):
        """Validate and clean observation data."""
        for k, v in observations.items():
            if isinstance(v, list):
                v = [None if x == "" else x for x in v]
            observations[k] = v
        return observations

    def __getitem__(self, key: int) -> list[Optional[float | int]]:
        """Get observations for a specific period."""
        return self.observations[key]

    @staticmethod
    def parse_key(key: str) -> list[int]:
        """Parse a key string into a list of integers."""
        return [int(x) for x in key.split(":")]

    @staticmethod
    def map_observation(
        key: str | list[int], observation: list[Optional[float | int]]
    ) -> dict[int, Optional[float | int]]:
        """Map a single observation to a dictionary with the period as key."""
        if isinstance(key, str):
            key = Series.parse_key(key)
        return dict(zip(key, observation))

    def map_observations(
        self, series_key: str
    ) -> dict[int, dict[int, Optional[float | int]]]:
        """Map observations from another series to this series."""
        parsed_key = self.parse_key(series_key)
        return {
            k: self.map_observation(key=parsed_key, observation=v)
            for k, v in self.observations.items()
        }

    def get_observation_periods(self) -> list[int]:
        """Get all observation periods (time points) for this series."""
        return list(self.observations.keys())

    def get_latest_observation(
        self,
    ) -> Optional[tuple[int, list[Optional[float | int]]]]:
        """Get the latest observation (highest period key)."""
        if not self.observations:
            return None
        latest_period = max(self.observations.keys())
        return latest_period, self.observations[latest_period]

    def get_earliest_observation(
        self,
    ) -> Optional[tuple[int, list[Optional[float | int]]]]:
        """Get the earliest observation (lowest period key)."""
        if not self.observations:
            return None
        earliest_period = min(self.observations.keys())
        return earliest_period, self.observations[earliest_period]

    def get_non_null_observations(self) -> dict[int, list[Optional[float | int]]]:
        """Get observations that contain at least one non-null value."""
        filtered = {}
        for period, values in self.observations.items():
            if any(v is not None for v in values):
                filtered[period] = values
        return filtered

    def get_observation_summary(self) -> dict[str, Any]:
        """Get a summary of observations in this series."""
        non_null_obs = self.get_non_null_observations()
        all_values = [
            v for obs in self.observations.values() for v in obs if v is not None
        ]

        summary: dict[str, Any] = {
            "total_periods": len(self.observations),
            "periods_with_data": len(non_null_obs),
            "total_values": sum(len(obs) for obs in self.observations.values()),
            "non_null_values": len(all_values),
            "period_range": (
                min(self.observations.keys()),
                max(self.observations.keys()),
            )
            if self.observations
            else None,
            "attribute_count": len(
                [attr for attr in self.attributes if attr is not None]
            ),
            "annotation_count": len(self.annotations),
        }

        if all_values:
            summary.update(
                {
                    "min_value": min(all_values),
                    "max_value": max(all_values),
                    "avg_value": sum(all_values) / len(all_values),
                }
            )

        return summary

    def has_attribute(self, attribute_ref: int) -> bool:
        """Check if this series has a specific attribute reference."""
        return attribute_ref in self.attributes

    def has_annotation(self, annotation_ref: int) -> bool:
        """Check if this series has a specific annotation reference."""
        return annotation_ref in self.annotations
