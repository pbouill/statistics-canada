"""
WDS Geographic Entity System

Provides a comprehensive system for working with Statistics Canada geographic data,
including location identification, coordinate translation, and data retrieval.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import pandas as pd
import numpy as np

from .client import Client as WDS
from .coordinate import create_enhanced_demographic_dataframe
from .models.datapoint import DataPoint
from ..enums.auto.wds.status import Status
from ..enums.auto.wds.symbol import Symbol
from ..enums.auto.wds.scalar import Scalar


@dataclass
class GeographicEntity:
    """Represents a geographic entity with its WDS metadata and coordinate system."""

    member_id: int
    name: str | None = None
    population: int | None = None
    coordinate: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self):
        """Generate coordinate if not provided."""
        if self.coordinate is None:
            self.coordinate = f"{self.member_id}.1.0.0.0.0.0.0.0.0"

    @classmethod
    async def from_member_id(
        cls, member_id: int, client: WDS | None = None
    ) -> GeographicEntity:
        """Create a GeographicEntity by discovering its properties from the WDS API."""
        if client is None:
            client = WDS()

        # Get population data to validate the member ID
        coordinate = f"{member_id}.1.0.0.0.0.0.0.0.0"

        # Try multiple product IDs to find one that works
        product_ids = [98100001, 98100002, 98100004]

        for product_id in product_ids:
            try:
                result = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
                    product_id=product_id, coordinate=coordinate, n=1
                )

                data = (
                    result.vectorDataPoint if hasattr(result, "vectorDataPoint") else []
                )
                if data and len(data) > 0:
                    population = data[0].value if data[0].value is not None else 0
                    return cls(
                        member_id=member_id,
                        population=int(population),
                        coordinate=coordinate,
                    )

            except Exception:
                continue  # Try next product ID

        # Return basic entity even if we can't get population
        return cls(member_id=member_id)

    @classmethod
    async def from_name(
        cls, name: str, client: WDS | None = None
    ) -> GeographicEntity | None:
        """Find a GeographicEntity by searching for a location name."""
        # This would require a lookup table or search functionality
        # For now, we'll return None and suggest using the discovery tools
        return None

    async def get_population_data(
        self, client: WDS | None = None, periods: int = 1
    ) -> list[DataPoint]:
        """Get population data for this geographic entity."""
        if client is None:
            client = WDS()

        # Try multiple product IDs in order of preference
        product_ids = [
            98100001,  # Population estimates (works for higher-level geographies)
            98100002,  # Census population (works for more geographies)
            98100004,  # Census households (backup for some areas)
        ]

        for product_id in product_ids:
            try:
                result = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
                    product_id=product_id, coordinate=self.coordinate or "", n=periods
                )

                # Check if we got valid data
                if (
                    hasattr(result, "vectorDataPoint")
                    and result.vectorDataPoint
                    and len(result.vectorDataPoint) > 0
                ):
                    return result.vectorDataPoint

            except Exception:
                continue  # Try next product ID

        return []  # No data found in any product ID

    async def get_data_as_array(
        self, client: WDS | None = None, periods: int = 10
    ) -> np.ndarray:
        """Get population data as a numpy array."""
        data = await self.get_population_data(client, periods)
        values = [float(dp.value) if dp.value is not None else 0.0 for dp in data]
        return np.array(values)

    async def get_data_as_dataframe(
        self,
        client: WDS | None = None,
        periods: int = 10,
        include_quality_info: bool = True,
    ) -> pd.DataFrame:
        """Get population data as a pandas DataFrame with enriched enum information."""
        data = await self.get_population_data(client, periods)

        records = []
        for dp in data:
            # Convert enum codes to meaningful descriptions
            status_desc = None
            if dp.statusCode:
                if hasattr(dp.statusCode, "name"):
                    status_desc = dp.statusCode.name.replace("_", " ").title()
                else:
                    status_desc = f"Status {dp.statusCode}"

            symbol_desc = None
            if dp.symbolCode and dp.symbolCode != Symbol.NONE:
                if hasattr(dp.symbolCode, "name"):
                    symbol_desc = dp.symbolCode.name.replace("_", " ").title()
                else:
                    symbol_desc = f"Symbol {dp.symbolCode}"

            scalar_desc = None
            if dp.scalarFactorCode:
                if hasattr(dp.scalarFactorCode, "name"):
                    scalar_desc = dp.scalarFactorCode.name.replace("_", " ").title()
                else:
                    scalar_desc = f"Scalar {dp.scalarFactorCode}"

            record = {
                "ref_date": dp.refPer,
                "value": float(dp.value) if dp.value is not None else None,
                "status_code": dp.statusCode.value
                if hasattr(dp.statusCode, "value")
                else dp.statusCode,
                "status": status_desc,
                "symbol_code": dp.symbolCode.value
                if hasattr(dp.symbolCode, "value")
                else dp.symbolCode,
                "symbol": symbol_desc,
                "scalar_code": dp.scalarFactorCode.value
                if hasattr(dp.scalarFactorCode, "value")
                else dp.scalarFactorCode,
                "scalar": scalar_desc,
                "member_id": self.member_id,
                "location": self.name,
                "coordinate": self.coordinate,
                "release_time": dp.releaseTime,
                "frequency": dp.frequencyCode.name
                if hasattr(dp.frequencyCode, "name")
                else dp.frequencyCode,
            }

            # Add human-readable quality information if requested
            if include_quality_info:
                record["quality_info"] = self.get_data_quality_info(dp)

            records.append(record)

        return pd.DataFrame(records)

    def __str__(self) -> str:
        name_part = f" ({self.name})" if self.name else ""
        pop_part = f", Population: {self.population:,}" if self.population else ""
        return f"Member ID {self.member_id}{name_part}{pop_part}"

    def __repr__(self) -> str:
        return f"GeographicEntity(member_id={self.member_id}, name={self.name!r}, population={self.population})"

    async def get_demographic_dataframe(
        self,
        demographic_type: str = "age_gender",
        census_year: int = 2021,
        client: WDS | None = None,
    ) -> pd.DataFrame:
        """
        Get demographic breakdown data as a clean, enum-based pandas DataFrame.

        Uses the enhanced coordinate system and consistent enum-based columns.

        Args:
            demographic_type: Type of demographic data to retrieve:
                - "age_gender": Age and gender breakdowns (product 98100020)
                - "age_broad": Broad age groups by gender (product 98100030)
            census_year: Census year (2016 or 2021)
            client: WDS client to use

        Returns:
            pandas.DataFrame: Clean demographic data with enum-based status/symbol columns
        """
        if client is None:
            from statscan.wds.client import Client

            client = Client()

        # Map demographic types to WDS product IDs
        product_map = {
            "age_gender": 98100020,  # Age (single years), average/median age by gender
            "age_broad": 98100030,  # Broad age groups by gender
        }

        if demographic_type not in product_map:
            raise ValueError(
                f"Unknown demographic_type: {demographic_type}. Available: {list(product_map.keys())}"
            )

        product_id = product_map[demographic_type]

        # Use enhanced DataFrame creation
        return await create_enhanced_demographic_dataframe(
            entity_member_id=self.member_id,
            entity_name=self.name or f"Member {self.member_id}",
            product_id=product_id,
            demographic_type=demographic_type,
            client=client,
            census_year=census_year,
            max_characteristics=20,  # Limit for performance
        )

    def get_data_quality_info(self, data_point: DataPoint) -> str:
        """Get a human-readable description of data point quality and symbols."""
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
