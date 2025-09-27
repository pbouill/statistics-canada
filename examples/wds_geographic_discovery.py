#!/usr/bin/env python3
"""
WDS Geographic Member ID Discovery Tool

This tool helps discover and validate WDS geographic member IDs for the population cube.
It can test ranges of member IDs to find valid locations and their names.
"""

import asyncio
import argparse
import json
import sys
from typing import Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, ".")

from statscan.wds.client import Client
from httpx import Timeout


# Population measure constants for coordinate building
POPULATION_2021 = 1
PRIVATE_DWELLINGS_2021 = 2
POPULATION_DENSITY_PER_KM2 = 3


class WDSGeographicDiscovery:
    """Tool for discovering WDS geographic member IDs"""

    def __init__(self) -> None:
        self.client: Optional[Client] = None
        self.population_cube_id = 98100002
        self.discovered_locations: list[dict[str, Any]] = []

    async def initialize(self) -> None:
        """Initialize the WDS client"""
        timeout = Timeout(30.0)
        self.client = Client(timeout=timeout)

    def build_coordinate(self, member_id: int, measure: int = POPULATION_2021) -> str:
        """Build coordinate string for testing"""
        return f"{member_id}.{measure}.0.0.0.0.0.0.0.0"

    async def test_member_id(
        self, member_id: int, verbose: bool = False
    ) -> dict[str, Any] | None:
        """
        Test if a member ID is valid and return location info

        Returns:
            Dict with location info if valid, None if invalid
        """
        if not self.client:
            return None

        coordinate = self.build_coordinate(member_id)

        try:
            data = await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                product_id=self.population_cube_id, coordinate=coordinate, n=1
            )

            if data and data.vectorDataPoint and len(data.vectorDataPoint) > 0:
                point = data.vectorDataPoint[0]

                location_info = {
                    "member_id": member_id,
                    "coordinate": coordinate,
                    "population_2021": int(point.value),
                    "reference_date": str(point.refPer),
                    "release_time": str(point.releaseTime),
                    "valid": True,
                }

                if verbose:
                    print(f"✅ {member_id}: Population = {int(point.value):,}")

                return location_info
            else:
                if verbose:
                    print(f"❌ {member_id}: No data")
                return None

        except Exception as e:
            if verbose:
                print(f"❌ {member_id}: Error - {str(e)[:50]}...")
            return None

    async def discover_range(
        self, start_id: int, end_id: int, verbose: bool = True
    ) -> list[dict[str, Any]]:
        """
        Discover valid member IDs in a range

        Args:
            start_id: Starting member ID
            end_id: Ending member ID (inclusive)
            verbose: Print progress

        Returns:
            List of valid location info dictionaries
        """
        print(f"🔍 Discovering member IDs in range {start_id} to {end_id}...")

        valid_locations: list[dict[str, Any]] = []
        total_tested = 0

        for member_id in range(start_id, end_id + 1):
            total_tested += 1

            if verbose and total_tested % 100 == 0:
                print(
                    f"   Tested {total_tested}/{end_id - start_id + 1} IDs, found {len(valid_locations)} valid"
                )

            location_info = await self.test_member_id(member_id, verbose=False)
            if location_info:
                valid_locations.append(location_info)
                if verbose:
                    print(
                        f"✅ Found {member_id}: Population = {location_info['population_2021']:,}"
                    )

        print(
            f"\\n📊 Discovery complete: {len(valid_locations)} valid locations found out of {total_tested} tested"
        )
        return valid_locations

    async def discover_major_cities(self) -> list[dict[str, Any]]:
        """
        Discover major cities by testing likely population ranges

        Major cities typically have populations > 100,000
        """
        print("🏙️  Discovering major cities (population > 100,000)...")

        # Test a broader range to find major population centers
        all_locations = await self.discover_range(1, 5000, verbose=False)

        # Filter for major cities
        major_cities = [loc for loc in all_locations if loc["population_2021"] > 100000]

        major_cities.sort(key=lambda x: x["population_2021"], reverse=True)

        print(f"\\n🏆 Found {len(major_cities)} major cities:")
        for city in major_cities:
            print(
                f"   Member ID {city['member_id']}: {city['population_2021']:,} people"
            )

        return major_cities

    async def test_known_locations(self) -> list[dict[str, Any]]:
        """Test some known/suspected member IDs"""

        print("🧪 Testing known/suspected member IDs...")

        # Known working
        known_ids = [2314]  # Saugeen Shores

        # Suspected major cities (educated guesses)
        suspected_ids = [
            535,  # Previously tested
            1,  # Often used for "Canada" or first entry
            100,  # Round numbers often used
            500,
            1000,
            1001,  # Toronto might be early in list
            1002,
            1500,
            2000,
            2500,
            3000,
        ]

        test_ids = known_ids + suspected_ids
        results = []

        for member_id in test_ids:
            location_info = await self.test_member_id(member_id, verbose=True)
            if location_info:
                results.append(location_info)

        return results

    def generate_enum_code(self, locations: list[dict[str, Any]]) -> str:
        """Generate enum code for discovered locations"""

        # Sort by population (largest first)
        sorted_locations = sorted(
            locations, key=lambda x: x["population_2021"], reverse=True
        )

        enum_entries = []
        for loc in sorted_locations:
            member_id = loc["member_id"]
            population = loc["population_2021"]

            # Generate a reasonable enum name (we don't have location names from API)
            enum_name = f"LOCATION_{member_id}"

            enum_entries.append(
                f"    {enum_name} = {member_id}  # Population: {population:,}"
            )

        enum_code = f"""
# Discovered WDS Geographic Locations
# Generated by WDS Geographic Discovery Tool

class DiscoveredWDSGeographic(IntEnum):
    \"\"\"
    Discovered geographic locations by WDS Member ID for Population cube (98100002).
    
    These locations were discovered through API testing and validation.
    \"\"\"
    
{chr(10).join(enum_entries)}
"""

        return enum_code

    def save_results(self, locations: list[dict[str, Any]], filename: str):
        """Save discovery results to JSON file"""
        with open(filename, "w") as f:
            json.dump(locations, f, indent=2)
        print(f"💾 Results saved to {filename}")


async def main():
    """Main discovery process"""

    parser = argparse.ArgumentParser(description="Discover WDS geographic member IDs")

    parser.add_argument(
        "--range",
        "-r",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Test range of member IDs (e.g., --range 1 1000)",
    )
    parser.add_argument(
        "--known",
        "-k",
        action="store_true",
        help="Test known/suspected member IDs only",
    )
    parser.add_argument(
        "--major-cities",
        "-m",
        action="store_true",
        help="Discover major cities (population > 100K)",
    )
    parser.add_argument("--test-id", "-t", type=int, help="Test a specific member ID")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="scratch/discovered_locations.json",
        help="Output file for results (default: scratch/discovered_locations.json)",
    )
    parser.add_argument(
        "--generate-enum",
        "-g",
        action="store_true",
        help="Generate enum code for discovered locations",
    )

    args = parser.parse_args()

    discovery = WDSGeographicDiscovery()
    await discovery.initialize()

    all_results = []

    # Test specific ID
    if args.test_id:
        print(f"🧪 Testing member ID {args.test_id}...")
        result = await discovery.test_member_id(args.test_id, verbose=True)
        if result:
            all_results.append(result)

    # Test known locations
    elif args.known or not any([args.range, args.major_cities, args.test_id]):
        results = await discovery.test_known_locations()
        all_results.extend(results)

    # Test range
    elif args.range:
        start_id, end_id = args.range
        results = await discovery.discover_range(start_id, end_id)
        all_results.extend(results)

    # Discover major cities
    elif args.major_cities:
        results = await discovery.discover_major_cities()
        all_results.extend(results)

    # Save results
    if all_results:
        discovery.save_results(all_results, args.output)

        if args.generate_enum:
            enum_code = discovery.generate_enum_code(all_results)
            print("\\n📝 Generated enum code:")
            print("=" * 60)
            print(enum_code)

    print("\\n🎯 Discovery Summary:")
    print(f"   • Found {len(all_results)} valid locations")
    if all_results:
        total_population = sum(loc["population_2021"] for loc in all_results)
        print(f"   • Total population: {total_population:,}")
        max_pop = max(all_results, key=lambda x: x["population_2021"])
        print(
            f"   • Largest location: Member ID {max_pop['member_id']} ({max_pop['population_2021']:,} people)"
        )


if __name__ == "__main__":
    asyncio.run(main())
