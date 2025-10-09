"""WDS Geographic Entity System.

Provides a data container for Statistics Canada geographic entities.
All API operations are handled by the Client class to avoid circular dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..enums.auto.wds.scalar import Scalar
from ..enums.auto.wds.status import Status
from ..enums.auto.wds.symbol import Symbol
from .models.datapoint import DataPoint


@dataclass
class GeographicEntity:
    """Represents a geographic entity with its WDS metadata.

    This is a pure data container. Use Client methods to fetch data for an entity.
    """

    member_id: int
    name: str | None = None
    population: int | None = None
    coordinate: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Generate coordinate if not provided."""
        if self.coordinate is None:
            self.coordinate = f"{self.member_id}.1.0.0.0.0.0.0.0.0"

    def __str__(self) -> str:
        """Return human-readable string representation of the geographic entity."""
        name_part = f" ({self.name})" if self.name else ""
        pop_part = f", Population: {self.population:,}" if self.population else ""
        return f"Member ID {self.member_id}{name_part}{pop_part}"

    def __repr__(self) -> str:
        """Return detailed string representation for debugging."""
        return (
            f"GeographicEntity(member_id={self.member_id}, "
            f"name={self.name!r}, population={self.population})"
        )

    @staticmethod
    def get_data_quality_info(data_point: DataPoint) -> str:  # noqa: PLR0912
        """Get a human-readable description of data point quality and symbols.

        This is a utility method that doesn't require API access.
        """
        parts = []

        # Status information (data quality)
        if data_point.statusCode:
            if hasattr(data_point.statusCode, "name"):
                status_name = data_point.statusCode.name.replace("_", " ").lower()
            else:
                status_name = f"status {data_point.statusCode}"
            if data_point.statusCode == Status.NORMAL:
                parts.append("✅ Normal quality")
            elif data_point.statusCode in [
                Status.DATA_QUAL_EXCELLENT,
                Status.DATA_QUAL_VERY_GOOD,
                Status.DATA_QUAL_GOOD,
            ]:
                parts.append(f"✅ {status_name.title()}")
            elif data_point.statusCode == Status.DATA_QUAL_ACCEPT:
                parts.append(f"⚠️ {status_name.title()}")
            elif data_point.statusCode == Status.USE_WITH_CAUTION:
                parts.append(f"⚠️ {status_name.title()}")
            elif data_point.statusCode == Status.TOO_UNRELIABLE_TO_BE_PUB:
                parts.append(f"❌ {status_name.title()}")
            else:
                parts.append(f"ℹ️ {status_name.title()}")

        # Symbol information (preliminary, revised, etc.)
        if data_point.symbolCode and data_point.symbolCode != Symbol.NONE:
            if hasattr(data_point.symbolCode, "name"):
                symbol_name = data_point.symbolCode.name.replace("_", " ").lower()
                parts.append(f"📝 {symbol_name.title()}")

        # Scalar factor
        if data_point.scalarFactorCode and data_point.scalarFactorCode != Scalar.UNITS:
            if hasattr(data_point.scalarFactorCode, "name"):
                scalar_name = data_point.scalarFactorCode.name.replace("_", " ").lower()
                parts.append(f"📊 In {scalar_name}")

        return " | ".join(parts) if parts else "✅ Standard data"
