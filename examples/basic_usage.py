#!/usr/bin/env python3
"""Statistics Canada WDS API - Basic Usage Examples.

This example demonstrates the fundamental patterns for using the Statistics Canada
Web Data Service (WDS) API through the statscan package.

Key Concepts:
- WDS client initialization and basic API calls
- Product discovery and cube metadata retrieval
- Simple data requests using coordinates
- Working with WDS enums and response parsing
"""

import asyncio
import logging

from statscan.enums.auto.wds.frequency import Frequency
from statscan.enums.auto.wds.product_id import ProductID
from statscan.wds.client import Client

logger = logging.getLogger(__name__)


async def basic_api_usage():
    """Demonstrate basic WDS API patterns."""
    # Initialize client
    client = Client()

    # 1. Discover available products

    # Get basic population cube metadata
    population_product = (
        ProductID.POP_AND_DWEL_COUNTS_CAN_PROV_AND_TERR_CEN_METRO_AREAS_AND_CEN_AGGLOMERATIONS
    )
    metadata = await client.get_cube_metadata(product_id=population_product.value)


    # 2. Simple coordinate-based data request

    # Get Canada total population for 2021
    coordinates = "1.1.1.1.1.1.1.1.1.1"  # Canada, both sexes, total age, 2021
    periods = 1  # Latest period only

    data_response = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
        product_id=population_product.value, coordinate=coordinates, periods=periods
    )

    if data_response["status"] == "SUCCESS":
        observations = data_response["object"]
        if observations:
            observations[0]
        else:
            pass
    else:
        pass

    # 3. Explore cube structure

    # Show dimension information
    dimensions = metadata["object"]["dimension"]
    for _i, dim in enumerate(dimensions[:3]):  # Show first 3 dimensions
        if dim["member"]:
            pass



async def working_with_enums():
    """Demonstrate using WDS enums for type-safe API calls."""
    # Use enums for better code maintainability

    # Show some census-related products
    census_products = [
        (
            ProductID.POP_AND_DWEL_COUNTS_CAN_PROV_AND_TERR_CEN_METRO_AREAS_AND_CEN_AGGLOMERATIONS,  # noqa: E501
            "Population & Dwellings",
        ),
    ]

    for _product_enum, _description in census_products:
        pass

    # Demonstrate frequency enum usage
    frequency_examples = [Frequency.ANNUAL, Frequency.QUARTERLY, Frequency.MONTHLY]

    for _freq in frequency_examples:
        pass


async def error_handling_patterns():
    """Show proper error handling for WDS API calls."""
    client = Client()

    try:
        # Example of handling invalid product ID
        response = await client.get_cube_metadata(product_id=99999999)

        if response["status"] != "SUCCESS":
            pass
        else:
            pass

    except Exception as e:
        logger.info("Expected error for invalid product ID: %s", e)

    try:
        # Example of handling invalid coordinates
        response = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
            product_id=ProductID.POPULATION_AND_DWELLINGS_COUNTS_CANADA_PROVINCES_TERRITORIES_CENSUS_METROPOLITAN_AREAS_AND_CENSUS_AGGLOMERATIONS_INCLUDING_PARTS.value,
            coordinate="999.999.999",  # Invalid coordinate format
            periods=1,
        )

        if response["status"] != "SUCCESS":
            pass

    except Exception as e:
        logger.info("Expected error for invalid coordinate: %s", e)



async def main():
    """Run all basic usage examples."""
    await basic_api_usage()
    await working_with_enums()
    await error_handling_patterns()



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
