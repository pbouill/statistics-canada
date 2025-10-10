#!/usr/bin/env python3
"""WDS Client Overview - Complete functionality demonstration.

This example shows all the capabilities of the main WDS Client class.
"""

import asyncio
import logging

from statscan.wds.client import Client

logger = logging.getLogger(__name__)


async def demonstrate_client_capabilities():
    """Demonstrate the complete Client functionality."""
    # Initialize single client for everything
    client = Client()

    # 1. Basic population lookup

    try:
        await client.get_population(2314)

        # Try name-based lookup (requires metadata)
        population_by_name = await client.get_population("Canada")
        if population_by_name:
            pass
        else:
            pass

    except Exception as e:
        logger.warning("Population lookup failed: %s", e)

    # 2. Location search

    try:
        # Search doesn't work yet because it needs metadata, but shows the API
        results = await client.search_locations("saugeen")
        if results:
            for _member_id, _name in results[:5]:
                pass
        else:
            pass

    except Exception as e:
        logger.warning("Location search failed: %s", e)

    # 3. Data in different formats

    member_id = 2314  # Saugeen Shores

    try:
        # Population only
        await client.get_location_data(member_id, format="population")

        # Geographic entity
        await client.get_location_data(member_id, format="entity")

        # DataFrame
        df = await client.get_location_data(member_id, format="dataframe", periods=3)
        if df is not None and len(df) > 0:
            pass

        # Array
        array = await client.get_location_data(member_id, format="array", periods=5)
        if array is not None:
            pass

    except Exception as e:
        logger.warning("Location data retrieval failed: %s", e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(demonstrate_client_capabilities())
