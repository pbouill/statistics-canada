#!/usr/bin/env python3
"""Statistics Canada WDS API - Fuzzy Search for Demographic Data.

This example demonstrates how to use fuzzy search functionality to find
geographic locations and extract demographic data, even with typos or
partial names.

Real-world Use Case: Finding and analyzing Saugeen Shores demographics
- Fuzzy search for municipality by name (handles typos)
- Language-aware searching (English/French)
- Population and age distribution analysis
- Demographic data extraction without knowing exact codes

Key Features Demonstrated:
1. Fuzzy geographic name matching
2. Bilingual enum searching
3. Census data extraction via full table download
4. DataFrame-based demographic analysis
5. Error-tolerant search patterns
"""

import asyncio
import sys
import traceback
from typing import Any

from statscan.enums.auto.census_subdivision import CensusSubdivision
from statscan.util.search import fuzzy_search_objects
from statscan.wds.client import Client
from statscan.wds.requests import ResponseLanguage


def get_searchable_text(member, language: str = "en") -> str:
    """Extract searchable text from an enum member.

    Args:
        member: Enum member with __doc_en__ and __doc_fr__ attributes
        language: "en" for English, "fr" for French

    Returns:
        The appropriate language text for fuzzy searching

    """
    if language.lower() == "fr":
        return getattr(member, "__doc_fr__", str(member.name))
    return getattr(member, "__doc_en__", str(member.name))


def search_municipality(
    query: str, language: str = "en", n: int = 5, cutoff: float = 0.6
) -> list[tuple[CensusSubdivision, float]]:
    """Search for municipalities using fuzzy matching.

    Args:
        query: Search query (can have typos, partial matches)
        language: "en" for English, "fr" for French
        n: Maximum number of results to return
        cutoff: Minimum similarity score (0.0-1.0)

    Returns:
        List of tuples: (CensusSubdivision member, match score)

    Examples:
        >>> # Find with typo
        >>> results = search_municipality("Saugeen")
        >>> results[0][0].value  # Returns the GeoCode
        3541024

        >>> # Find with partial French name
        >>> results = search_municipality("Terre-Neuve", language="fr")

    """
    return fuzzy_search_objects(
        query=query,
        objects=list(CensusSubdivision),
        key_func=lambda m: get_searchable_text(m, language),
        n=n,
        cutoff=cutoff,
    )


async def get_municipality_demographics(
    municipality_name: str, language: str = "en"
) -> dict[str, Any]:
    """Get demographic data for a municipality using fuzzy search.

    This function demonstrates the simplified workflow using the Client's
    built-in fuzzy filtering capabilities.

    Args:
        municipality_name: Name to search for (tolerates typos)
        language: Search language ("en" or "fr")

    Returns:
        Dictionary containing demographic statistics and the DataFrame

    Raises:
        ValueError: If municipality not found

    """
    print(f'🔍 Getting demographics for: "{municipality_name}" ({language})...')
    print()

    # Step 1: Initialize client
    client = Client()

    # Step 2: Census Profile product (Population and dwelling counts)
    # Product ID 98100002: Census subdivisions (municipalities)
    product_id = 98100002

    # Step 3: Get metadata to confirm it's a snapshot cube
    metadata = await client.get_cube_metadata(product_id=product_id)
    print(f"📊 Cube: {metadata.cubeTitleEn}")
    print(f"   Supports coordinate queries: {metadata.supports_coordinate_queries}")
    print()

    # Step 4: Use the enhanced get_dataframe() with fuzzy filtering
    # The client will:
    # - Download the full census table
    # - Fuzzy match "geography" to the actual column name (probably "GEO")
    # - Fuzzy match "Saugeen Shores" to actual municipality names
    # - Return only the matching rows
    print(f'⬇️  Downloading and filtering for "{municipality_name}"...')

    lang_enum = ResponseLanguage.EN if language == "en" else ResponseLanguage.FR

    df = await client.get_dataframe(
        product_id=product_id,
        language=lang_enum,
        geo=municipality_name,  # Fuzzy match on GEO column
    )

    print(f"✅ Found {len(df):,} rows of data")
    print()

    if df.empty:
        raise ValueError(
            f'No data found for "{municipality_name}". '
            f"The fuzzy match may have failed. Try a different spelling."
        )

    # Step 5: Extract demographic information
    demographics = {
        "municipality": municipality_name,
        "total_rows": len(df),
        "columns": df.columns.tolist(),
    }

    # Show what we found
    print("📋 Available Data Columns:")
    for col in df.columns:
        print(f"   • {col}")
    print()

    # Extract key statistics from the single row
    if len(df) == 1:
        row = df.iloc[0]
        print("📊 Demographics for", row.get("GEO", municipality_name))
        print("-" * 80)

        # Population statistics
        pop_2021_col = [c for c in df.columns if "Population, 2021" in c]
        pop_2016_col = [c for c in df.columns if "Population, 2016" in c]
        pop_change_col = [c for c in df.columns if "Population percentage change" in c]

        if pop_2021_col:
            print(f"   Population (2021): {row[pop_2021_col[0]]:,.0f}")
        if pop_2016_col:
            print(f"   Population (2016): {row[pop_2016_col[0]]:,.0f}")
        if pop_change_col:
            print(f"   Population Change (2016-2021): {row[pop_change_col[0]]}%")

        print()

        # Dwelling statistics
        dwellings_2021_col = [
            c for c in df.columns if "Total private dwellings, 2021" in c
        ]
        dwellings_occupied_col = [
            c
            for c in df.columns
            if "Private dwellings occupied by usual residents, 2021" in c
        ]

        if dwellings_2021_col:
            print(
                f"   Total Private Dwellings (2021): "
                f"{row[dwellings_2021_col[0]]:,.0f}"
            )
        if dwellings_occupied_col:
            print(
                f"   Occupied Dwellings (2021): "
                f"{row[dwellings_occupied_col[0]]:,.0f}"
            )

        print()

        # Geographic statistics
        area_col = [c for c in df.columns if "Land area in square kilometres" in c]
        density_col = [
            c for c in df.columns if "Population density per square kilometre" in c
        ]

        if area_col:
            print(f"   Land Area (sq km): {row[area_col[0]]:,.2f}")
        if density_col:
            print(f"   Population Density (per sq km): {row[density_col[0]]:,.1f}")

        demographics["summary"] = {
            "population_2021": row[pop_2021_col[0]] if pop_2021_col else None,
            "population_2016": row[pop_2016_col[0]] if pop_2016_col else None,
            "population_change": row[pop_change_col[0]] if pop_change_col else None,
            "dwellings_total": (
                row[dwellings_2021_col[0]] if dwellings_2021_col else None
            ),
            "dwellings_occupied": (
                row[dwellings_occupied_col[0]] if dwellings_occupied_col else None
            ),
            "land_area_sqkm": row[area_col[0]] if area_col else None,
            "population_density": row[density_col[0]] if density_col else None,
        }

    demographics["dataframe"] = df

    return demographics


async def demo_fuzzy_search():
    """Demonstrate fuzzy search capabilities for demographic analysis."""
    print("=" * 80)
    print("🎯 FUZZY SEARCH FOR DEMOGRAPHIC DATA")
    print("=" * 80)
    print()
    print("This example shows how to:")
    print("1. Download census data with built-in fuzzy filtering")
    print("2. Handle typos in municipality names automatically")
    print("3. Extract demographic statistics from census tables")
    print()

    # Test cases with various spellings and typos
    test_queries = [
        "Saugeen Shores",  # Exact match
        "saugeen shores",  # Case insensitive
        "Saugen Shore",  # Typo tolerance
    ]

    for query in test_queries:
        print("\n" + "=" * 80)
        print(f"🔎 TEST: '{query}'")
        print("=" * 80)
        print()

        try:
            demographics = await get_municipality_demographics(query, language="en")

            print()
            print("=" * 80)
            print("✅ SUCCESS")
            print("=" * 80)
            print(f"Municipality: {demographics['municipality']}")
            print(f"Total rows: {demographics['total_rows']:,}")

            # Show summary if available
            if "summary" in demographics:
                print("\n" + "📊 DEMOGRAPHIC SUMMARY" + "\n" + "-" * 80)
                summary = demographics["summary"]
                min_value_for_formatting = 100
                for key, value in summary.items():
                    if value is not None:
                        key_display = key.replace("_", " ").title()
                        if (
                            isinstance(value, (int, float))
                            and value > min_value_for_formatting
                        ):
                            print(f"   {key_display}: {value:,.1f}")
                        else:
                            print(f"   {key_display}: {value}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            traceback.print_exc()

        print()


async def quick_demo():
    """Quick demonstration with just the Saugeen Shores search."""
    print("=" * 80)
    print("🎯 QUICK DEMO: Fuzzy Search for Saugeen Shores Demographics")
    print("=" * 80)
    print()

    # Show fuzzy search capabilities
    print("1️⃣  FUZZY SEARCH EXAMPLES")
    print("-" * 80)

    test_queries = [
        "Saugeen Shores",  # Exact
        "Saugeen",  # Partial
        "saugeen shores",  # Case insensitive
        "Saugen Shore",  # Typo
    ]

    for query in test_queries:
        matches = search_municipality(query, language="en", n=1)
        if matches:
            geo_code, score = matches[0]
            print(
                f"   Query: '{query:20s}' → {geo_code.name:40s} "
                f"(score: {score:.3f})"
            )

    print()
    print("2️⃣  SEARCH WITH DETAILS")
    print("-" * 80)
    print()
    print('Searching for "Saugeen Shores" with top 3 results:')
    print()

    matches = search_municipality("Saugeen Shores", language="en", n=3)
    for i, (geo_code, score) in enumerate(matches, 1):
        print(f"{i}. {geo_code.name:40s} (score: {score:.3f})")
        print(f"   Value: {geo_code.value}")
        print(f"   EN: {geo_code.__doc_en__}")
        print(f"   FR: {geo_code.__doc_fr__}")
        print()

    print()
    print("3️⃣  BILINGUAL SEARCH")
    print("-" * 80)
    print()

    # Show French search example
    fr_query = "Montréal"
    matches = search_municipality(fr_query, language="fr", n=3)
    print(f'French query: "{fr_query}"')
    for i, (geo_code, score) in enumerate(matches, 1):
        print(f"   {i}. {geo_code.name:35s} (score: {score:.3f})")

    print()
    print("=" * 80)
    print("✨ DEMOGRAPHIC DATA EXTRACTION")
    print("=" * 80)
    print()
    print("To extract full demographic data, run:")
    print("   python fuzzy_search_demographics.py --full")
    print()
    print("Note: This will download the complete census dataset (~1-2 minutes)")
    print("      and filter for the specific municipality.")
    print()
    print("=" * 80)
    print("💡 TIP: Use search_municipality() in your own scripts to find any")
    print("   Canadian municipality, even with typos or partial names!")
    print("=" * 80)


async def main():
    """Run main entry point for the fuzzy search demo."""
    if len(sys.argv) > 1 and sys.argv[1] == "--full":
        # Full demo with data extraction
        await demo_fuzzy_search()
    else:
        # Quick demo showing search capabilities
        await quick_demo()


if __name__ == "__main__":
    asyncio.run(main())
