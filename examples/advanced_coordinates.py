#!/usr/bin/env python3
"""Statistics Canada WDS API - Advanced Coordinate System Examples.

This example demonstrates sophisticated coordinate building and manipulation
for complex statistical queries using the WDS API.

Advanced Features:
- Multi-dimensional coordinate construction
- Parameter-based coordinate building
- Time series coordinate manipulation
- Complex filtering and data aggregation
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

from statscan.wds.client import Client

logger = logging.getLogger(__name__)


@dataclass
class CoordinateBuilder:
    """Advanced coordinate construction utility."""

    geography: str = "1"  # 1=Canada, 35=Ontario, etc.
    gender: str = "1"  # 1=Both, 2=Male, 3=Female
    age_group: str = "1"  # 1=All ages, 2=0-14, 3=15-64, etc.
    additional_dims: list[str] | None = None

    def __post_init__(self):
        """Initialize remaining dimensions to default value."""
        if self.additional_dims is None:
            self.additional_dims = ["1"] * 7  # Default remaining dimensions to "1"

    def build(self) -> str:
        """Build complete coordinate string."""
        dims = self.additional_dims if self.additional_dims is not None else ["1"] * 7
        coords = [self.geography, self.gender, self.age_group] + dims
        return ".".join(coords[:10])  # WDS coordinates are typically 10 dimensions

    def with_geography(self, geo_code: str | int) -> "CoordinateBuilder":
        """Create new builder with different geography."""
        new_builder = CoordinateBuilder(
            geography=str(geo_code),
            gender=self.gender,
            age_group=self.age_group,
            additional_dims=self.additional_dims.copy()
            if self.additional_dims
            else None,
        )
        return new_builder

    def with_gender(self, gender_code: str | int) -> "CoordinateBuilder":
        """Create new builder with different gender filter."""
        new_builder = CoordinateBuilder(
            geography=self.geography,
            gender=str(gender_code),
            age_group=self.age_group,
            additional_dims=self.additional_dims.copy()
            if self.additional_dims
            else None,
        )
        return new_builder

    def with_age_group(self, age_code: str | int) -> "CoordinateBuilder":
        """Create new builder with different age group."""
        new_builder = CoordinateBuilder(
            geography=self.geography,
            gender=self.gender,
            age_group=str(age_code),
            additional_dims=self.additional_dims.copy()
            if self.additional_dims
            else None,
        )
        return new_builder


class AdvancedCoordinateSystem:
    """Advanced coordinate manipulation and data analysis."""

    def __init__(self):
        """Initialize the coordinate system with a WDS client."""
        self.client = Client()

    async def multi_dimensional_analysis(
        self, product_id: int, base_coordinate: str
    ) -> dict[str, Any]:
        """Perform analysis across multiple dimensions simultaneously."""
        # Create coordinate variations
        builder = CoordinateBuilder()

        # Geographic variations
        geographic_variants = {
            "Canada": builder.with_geography("1"),
            "Ontario": builder.with_geography("35"),  # Assuming Ontario = 35
            "Quebec": builder.with_geography("24"),  # Assuming Quebec = 24
        }

        # Gender variations for each geography
        results = {}

        for geo_name, geo_builder in geographic_variants.items():
            geo_results = {}

            gender_variants = {
                "Total": geo_builder.with_gender("1"),
                "Male": geo_builder.with_gender("2"),
                "Female": geo_builder.with_gender("3"),
            }

            for gender_name, gender_builder in gender_variants.items():
                coordinate = gender_builder.build()

                try:
                    response = await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(  # noqa: E501
                        product_id=product_id, coordinate=coordinate, periods=1
                    )

                    if response["status"] == "SUCCESS" and response["object"]:
                        data = response["object"][0]
                        geo_results[gender_name] = {
                            "population": data["vectorDataPoint"],
                            "coordinate": coordinate,
                        }

                except Exception as e:
                    logger.debug(
                        "Failed to fetch data for %s/%s: %s", geo_name, gender_name, e
                    )

            results[geo_name] = geo_results

        return results

    async def time_series_coordinates(
        self, product_id: int, base_coordinate: str, periods: int = 5
    ) -> list[dict[str, Any]]:
        """Build coordinates for time series analysis."""
        try:
            # Get multiple periods of data
            response = (
                await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                    product_id=product_id, coordinate=base_coordinate, periods=periods
                )
            )

            if response["status"] == "SUCCESS" and response["object"]:
                time_series = response["object"]


                results = []
                for i, data_point in enumerate(time_series):
                    result = {
                        "period": data_point["refPer"],
                        "value": data_point["vectorDataPoint"],
                        "coordinate": base_coordinate,
                        "sequence": i + 1,
                    }
                    results.append(result)


                # Calculate growth rates
                if len(results) > 1:
                    latest = results[0]["value"]
                    previous = results[1]["value"]

                    if previous > 0:
                        ((latest - previous) / previous) * 100

                return results

        except Exception as e:
            logger.warning("Time series analysis failed: %s", e)

        return []

    async def parameter_based_queries(self, product_id: int) -> dict[str, Any]:
        """Demonstrate parameter-based coordinate construction."""
        # Define query parameters
        query_scenarios: list[dict[str, Any]] = [
            {
                "name": "National Overview",
                "params": {"geography": "1", "gender": "1", "age": "1"},
                "description": "Canada total population, all demographics",
            },
            {
                "name": "Youth Demographics (Male)",
                "params": {
                    "geography": "1",
                    "gender": "2",
                    "age": "2",
                },  # Assuming age group 2 = youth
                "description": "Canada male youth population",
            },
            {
                "name": "Working Age (Female)",
                "params": {
                    "geography": "1",
                    "gender": "3",
                    "age": "3",
                },  # Assuming age group 3 = working age
                "description": "Canada female working age population",
            },
        ]

        results = {}

        for scenario in query_scenarios:

            # Build coordinate from parameters
            params: dict[str, str] = scenario["params"]  # type: ignore
            coordinate = (
                f"{params['geography']}.{params['gender']}.{params['age']}"
                ".1.1.1.1.1.1.1"
            )

            try:
                response = (
                    await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                        product_id=product_id, coordinate=coordinate, periods=1
                    )
                )

                if response["status"] == "SUCCESS" and response["object"]:
                    data = response["object"][0]
                    result = {
                        "coordinate": coordinate,
                        "population": data["vectorDataPoint"],
                        "period": data["refPer"],
                        "parameters": params,
                    }
                    name: str = scenario["name"]  # type: ignore
                    results[name] = result

                else:
                    logger.debug("Query %s returned no data", scenario["name"])

            except Exception as e:
                logger.debug("Query %s failed: %s", scenario["name"], e)

        return results

    async def coordinate_validation_and_debugging(self, product_id: int) -> None:
        """Demonstrate coordinate validation techniques."""
        # Get cube metadata for validation
        metadata = await self.client.get_cube_metadata(product_id=product_id)

        if metadata["status"] != "SUCCESS":
            return

        cube = metadata["object"]
        dimensions = cube["dimension"]


        # Test various coordinate formats
        test_coordinates = [
            "1.1.1.1.1.1.1.1.1.1",  # Standard 10-dimension
            "1.1.1",  # Too short
            "1.1.1.1.1.1.1.1.1.1.1.1",  # Too long
            "999.999.999.999.999.999.999.999.999.999",  # Invalid values
        ]


        for coord in test_coordinates:
            try:
                response = (
                    await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                        product_id=product_id, coordinate=coord, periods=1
                    )
                )

                if response["status"] == "SUCCESS" and response["object"]:
                    logger.debug("Valid coordinate: %s", coord)
                else:
                    logger.debug("Invalid coordinate: %s", coord)

            except Exception as e:
                logger.debug("Coordinate test failed for %s: %s", coord, e)

        # Show dimension structure for reference
        for _i, _dim in enumerate(dimensions[:5]):  # Show first 5
            pass


async def advanced_aggregation_example():
    """Show complex data aggregation using coordinate manipulation."""
    coordinator = AdvancedCoordinateSystem()

    # Use population cube for demonstration
    product_id = 98100002  # Census population data


    # Multi-dimensional analysis
    analysis_results = await coordinator.multi_dimensional_analysis(
        product_id, "1.1.1.1.1.1.1.1.1.1"
    )

    # Calculate aggregated statistics
    if analysis_results:

        for _geography, data in analysis_results.items():
            if "Total" in data and "Male" in data and "Female" in data:
                total = data["Total"]["population"]
                male = data["Male"]["population"]
                female = data["Female"]["population"]

                if total > 0:
                    (male / total) * 100
                    (female / total) * 100



async def main():
    """Run advanced coordinate system examples."""
    coordinator = AdvancedCoordinateSystem()

    # Product for demonstrations
    product_id = 98100002  # Census population data
    base_coordinate = "1.1.1.1.1.1.1.1.1.1"  # Canada, total


    # Parameter-based queries
    await coordinator.parameter_based_queries(product_id)

    # Time series analysis
    await coordinator.time_series_coordinates(product_id, base_coordinate, periods=3)

    # Coordinate validation
    await coordinator.coordinate_validation_and_debugging(product_id)

    # Advanced aggregation
    await advanced_aggregation_example()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
