#!/usr/bin/env python3
"""Statistics Canada WDS API - Demographic Analysis Examples.

This example demonstrates practical demographic analysis using the WDS API.
Shows how to work with census data, compare populations, and analyze demographic trends.

Real-world Use Case: Analyzing population demographics for Saugeen Shores, Ontario
- Municipal population analysis
- Age and gender breakdowns
- Household composition studies
- Geographic comparisons
"""

import asyncio
import logging
from typing import Any

from statscan.enums.auto.wds.product_id import ProductID
from statscan.wds.client import Client

logger = logging.getLogger(__name__)


class DemographicAnalyzer:
    """Utility class for comprehensive demographic analysis."""

    def __init__(self):
        """Initialize the analyzer with a WDS client."""
        self.client = Client()

    async def get_population_summary(
        self, product_id: int, coordinates: list[str], location_name: str
    ) -> dict[str, Any]:
        """Get population summary for specified coordinates."""
        results = {}
        for coord in coordinates:
            try:
                response = (
                    await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                        product_id=product_id, coordinate=coord, periods=1
                    )
                )

                if response["status"] == "SUCCESS" and response["object"]:
                    data = response["object"][0]
                    results[coord] = {
                        "population": data["vectorDataPoint"],
                        "reference_date": data["refPer"],
                    }
                else:
                    logger.debug("No data returned for coordinate: %s", coord)

            except Exception as e:
                logger.warning("Failed to fetch population for %s: %s", coord, e)

        return results

    async def analyze_age_gender_demographics(
        self, location_coordinates: str
    ) -> dict[str, Any]:
        """Analyze age and gender demographics for a location."""
        # Use Age and Sex highlights product (Census data)
        product_id = 98100002  # Census population data

        # Get cube metadata to understand dimensions
        await self.client.get_cube_metadata(product_id=product_id)


        # Example coordinates for different age/gender breakdowns
        # Note: Actual coordinates depend on cube structure
        demo_coordinates = [
            f"{location_coordinates}.1.1.1.1.1.1.1.1.1",  # Total population
            f"{location_coordinates}.2.1.1.1.1.1.1.1.1",  # Male population
            f"{location_coordinates}.3.1.1.1.1.1.1.1.1",  # Female population
        ]

        results = {}
        labels = ["Total", "Male", "Female"]

        for coord, label in zip(demo_coordinates, labels, strict=False):
            try:
                response = (
                    await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                        product_id=product_id, coordinate=coord, periods=1
                    )
                )

                if response["status"] == "SUCCESS" and response["object"]:
                    data = response["object"][0]
                    results[label] = data["vectorDataPoint"]

            except Exception as e:
                logger.warning("Failed to fetch %s demographics: %s", label, e)

        return results

    async def household_analysis(self, location_coordinates: str) -> dict[str, Any]:
        """Analyze household composition and characteristics."""
        product_id = 98100003  # Census household data

        # Get metadata
        await self.client.get_cube_metadata(product_id=product_id)

        # Try to get household data
        try:
            response = (
                await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                    product_id=product_id,
                    coordinate=f"{location_coordinates}.1.1.1.1.1.1.1.1.1",
                    periods=1,
                )
            )

            if response["status"] == "SUCCESS" and response["object"]:
                data = response["object"][0]
                return {"total_households": data["vectorDataPoint"]}
            else:
                logger.debug("No household data returned")

        except Exception as e:
            logger.warning("Household analysis failed: %s", e)

        return {}

    async def create_demographic_report(
        self, location_name: str, coordinates: str
    ) -> dict[str, Any]:
        """Generate comprehensive demographic report."""
        report: dict[str, Any] = {
            "location": location_name,
            "coordinates": coordinates,
            "population": {},
            "demographics": {},
            "households": {},
        }

        # Population overview
        pop_product = 98100002  # Census population data

        population_data = await self.get_population_summary(
            pop_product, [coordinates], location_name
        )
        report["population"] = population_data

        # Age/gender demographics
        demographics = await self.analyze_age_gender_demographics(coordinates)
        report["demographics"] = demographics

        # Household analysis
        households = await self.household_analysis(coordinates)
        report["households"] = households

        # Summary statistics
        if demographics:
            total_pop = demographics.get("Total", 0)
            male_pop = demographics.get("Male", 0)
            female_pop = demographics.get("Female", 0)

            if total_pop > 0:
                if male_pop and female_pop:
                    pass

                if households and households.get("total_households"):
                    total_pop / households["total_households"]

        return report


async def saugeen_shores_case_study():
    """Real-world example: Analyzing Saugeen Shores, Ontario demographics."""
    analyzer = DemographicAnalyzer()

    # Saugeen Shores coordinates (example - actual coordinates need verification)
    # This represents: Ontario > Bruce County > Saugeen Shores
    saugeen_coordinates = "1.35.3539.001"  # Example coordinate structure

    # Generate comprehensive report
    report = await analyzer.create_demographic_report(
        "Saugeen Shores, ON", saugeen_coordinates
    )

    # Display findings
    if report.get("population"):

        if report.get("demographics"):
            total = report["demographics"].get("Total", 0)
            if total > 0:
                pass


    return report


async def comparative_analysis_example():
    """Compare multiple geographic areas."""
    analyzer = DemographicAnalyzer()

    # Compare different geographic levels
    locations = [
        ("Canada", "1.1.1.1.1.1.1.1.1.1"),
        ("Ontario", "1.35.1.1.1.1.1.1.1.1"),
        ("Bruce County", "1.35.3539.1.1.1.1.1.1.1"),  # Example
    ]

    # fmt: off
    product_id = (
        ProductID.
        POPULATION_AND_DWELLINGS_COUNTS_CANADA_PROVINCES_AND_TERRITORIES_CENSUS_METROPOLITAN_AREAS_AND_CENSUS_AGGLOMERATIONS_INCLUDING_PARTS.value
    )
    # fmt: on


    comparative_data = {}
    for name, coord in locations:
        results = await analyzer.get_population_summary(product_id, [coord], name)
        if results:
            comparative_data[name] = results[coord]

    # Calculate percentages
    min_locations_for_comparison = 2
    if len(comparative_data) >= min_locations_for_comparison:
        canada_pop = comparative_data.get("Canada", {}).get("population", 1)

        for location, data in comparative_data.items():
            if location != "Canada":
                population = data.get("population", 0)
                (population / canada_pop) * 100 if canada_pop > 0 else 0


async def main():
    """Run demographic analysis examples."""
    # Real-world case study
    await saugeen_shores_case_study()

    # Comparative analysis
    await comparative_analysis_example()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
