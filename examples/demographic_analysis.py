#!/usr/bin/env python3
"""
Statistics Canada WDS API - Demographic Analysis Examples

This example demonstrates practical demographic analysis using the WDS API.
Shows how to work with census data, compare populations, and analyze demographic trends.

Real-world Use Case: Analyzing population demographics for Saugeen Shores, Ontario
- Municipal population analysis
- Age and gender breakdowns  
- Household composition studies
- Geographic comparisons
"""

import asyncio
import pandas as pd
from typing import Any

from statscan.wds.client import Client
from statscan.enums.auto.wds.product_id import ProductID


class DemographicAnalyzer:
    """Utility class for comprehensive demographic analysis."""
    
    def __init__(self):
        self.client = Client()
    
    async def get_population_summary(self, product_id: int, coordinates: list[str], 
                                   location_name: str) -> dict[str, Any]:
        """Get population summary for specified coordinates."""
        print(f"\n📊 Population Summary: {location_name}")
        print("-" * 40)
        
        results = {}
        for coord in coordinates:
            try:
                response = await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                    product_id=product_id,
                    coordinate=coord,
                    periods=1
                )
                
                if response['status'] == 'SUCCESS' and response['object']:
                    data = response['object'][0]
                    results[coord] = {
                        'population': data['vectorDataPoint'],
                        'reference_date': data['refPer']
                    }
                    print(f"  Coordinate {coord}: {data['vectorDataPoint']:,} people")
                else:
                    print(f"  ⚠️  No data for coordinate {coord}")
                    
            except Exception as e:
                print(f"  ❌ Error with coordinate {coord}: {e}")
                
        return results
    
    async def analyze_age_gender_demographics(self, location_coordinates: str) -> dict[str, Any]:
        """Analyze age and gender demographics for a location."""
        print(f"\n👥 Age & Gender Analysis")
        print("-" * 40)
        
        # Use Age and Sex highlights product (Census data)
        product_id = 98100002  # Census population data
        
        # Get cube metadata to understand dimensions
        metadata = await self.client.get_cube_metadata(product_id=product_id)
        
        print(f"Analyzing demographics using Product ID: {product_id}")
        print(f"Cube: {metadata['object']['cubeTitleEn']}")
        
        # Example coordinates for different age/gender breakdowns
        # Note: Actual coordinates depend on cube structure
        demo_coordinates = [
            f"{location_coordinates}.1.1.1.1.1.1.1.1.1",  # Total population
            f"{location_coordinates}.2.1.1.1.1.1.1.1.1",  # Male population  
            f"{location_coordinates}.3.1.1.1.1.1.1.1.1",  # Female population
        ]
        
        results = {}
        labels = ["Total", "Male", "Female"]
        
        for coord, label in zip(demo_coordinates, labels):
            try:
                response = await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                    product_id=product_id,
                    coordinate=coord,
                    periods=1
                )
                
                if response['status'] == 'SUCCESS' and response['object']:
                    data = response['object'][0]
                    results[label] = data['vectorDataPoint']
                    print(f"  {label}: {data['vectorDataPoint']:,}")
                    
            except Exception as e:
                print(f"  ⚠️  Could not get {label} data: {e}")
        
        return results
    
    async def household_analysis(self, location_coordinates: str) -> dict[str, Any]:
        """Analyze household composition and characteristics."""
        print(f"\n🏠 Household Composition Analysis")
        print("-" * 40)
        
        product_id = 98100003  # Census household data
        
        # Get metadata
        metadata = await self.client.get_cube_metadata(product_id=product_id)
        print(f"Using: {metadata['object']['cubeTitleEn']}")
        
        # Try to get household data
        try:
            response = await self.client.get_data_from_cube_pid_coord_and_latest_n_periods(
                product_id=product_id,
                coordinate=f"{location_coordinates}.1.1.1.1.1.1.1.1.1",
                periods=1
            )
            
            if response['status'] == 'SUCCESS' and response['object']:
                data = response['object'][0]
                print(f"  Total Households: {data['vectorDataPoint']:,}")
                return {'total_households': data['vectorDataPoint']}
            else:
                print("  ⚠️  No household data available")
                
        except Exception as e:
            print(f"  ❌ Household analysis error: {e}")
            
        return {}
    
    async def create_demographic_report(self, location_name: str, coordinates: str) -> dict[str, Any]:
        """Generate comprehensive demographic report."""
        print(f"\n📋 Comprehensive Demographic Report: {location_name}")
        print("=" * 60)
        
        report: dict[str, Any] = {
            'location': location_name, 
            'coordinates': coordinates,
            'population': {},
            'demographics': {},
            'households': {}
        }
        
        # Population overview
        pop_product = 98100002  # Census population data
        
        population_data = await self.get_population_summary(
            pop_product, 
            [coordinates], 
            location_name
        )
        report['population'] = population_data
        
        # Age/gender demographics  
        demographics = await self.analyze_age_gender_demographics(coordinates)
        report['demographics'] = demographics
        
        # Household analysis
        households = await self.household_analysis(coordinates)
        report['households'] = households
        
        # Summary statistics
        if demographics:
            total_pop = demographics.get('Total', 0)
            male_pop = demographics.get('Male', 0) 
            female_pop = demographics.get('Female', 0)
            
            if total_pop > 0:
                print(f"\n📈 Summary Statistics:")
                print(f"  • Total Population: {total_pop:,}")
                if male_pop and female_pop:
                    print(f"  • Gender Distribution: {male_pop/total_pop*100:.1f}% Male, {female_pop/total_pop*100:.1f}% Female")
                
                if households and households.get('total_households'):
                    avg_household_size = total_pop / households['total_households']
                    print(f"  • Average Household Size: {avg_household_size:.1f} people")
        
        return report


async def saugeen_shores_case_study():
    """Real-world example: Analyzing Saugeen Shores, Ontario demographics."""
    print("🏘️  Case Study: Saugeen Shores, Ontario")
    print("=" * 60)
    print("Saugeen Shores is a town in Bruce County, Ontario")
    print("This example shows municipal-level demographic analysis\n")
    
    analyzer = DemographicAnalyzer()
    
    # Saugeen Shores coordinates (example - actual coordinates need verification)
    # This represents: Ontario > Bruce County > Saugeen Shores 
    saugeen_coordinates = "1.35.3539.001"  # Example coordinate structure
    
    # Generate comprehensive report
    report = await analyzer.create_demographic_report("Saugeen Shores, ON", saugeen_coordinates)
    
    # Display findings
    if report.get('population'):
        print(f"\n🎯 Key Findings:")
        print(f"  • Municipality: {report['location']}")
        print(f"  • Coordinate System: {report['coordinates']}")
        
        if report.get('demographics'):
            total = report['demographics'].get('Total', 0)
            if total > 0:
                print(f"  • Classification: Small-medium Ontario municipality ({total:,} residents)")
    
    print(f"\n💡 Next Steps:")
    print(f"  • Verify coordinate accuracy with Statistics Canada documentation") 
    print(f"  • Compare with neighboring municipalities")
    print(f"  • Analyze trends over multiple census periods")
    
    return report


async def comparative_analysis_example():
    """Example of comparing multiple geographic areas."""
    print("\n🔄 Comparative Analysis Example")
    print("=" * 60)
    
    analyzer = DemographicAnalyzer()
    
    # Compare different geographic levels
    locations = [
        ("Canada", "1.1.1.1.1.1.1.1.1.1"),
        ("Ontario", "1.35.1.1.1.1.1.1.1.1"), 
        ("Bruce County", "1.35.3539.1.1.1.1.1.1.1"),  # Example
    ]
    
    product_id = ProductID.POPULATION_AND_DWELLINGS_COUNTS_CANADA_PROVINCES_AND_TERRITORIES_CENSUS_METROPOLITAN_AREAS_AND_CENSUS_AGGLOMERATIONS_INCLUDING_PARTS.value
    
    print("Comparing population across geographic levels:")
    
    comparative_data = {}
    for name, coord in locations:
        results = await analyzer.get_population_summary(product_id, [coord], name)
        if results:
            comparative_data[name] = results[coord]
    
    # Calculate percentages
    if len(comparative_data) >= 2:
        print(f"\n📊 Comparative Statistics:")
        canada_pop = comparative_data.get('Canada', {}).get('population', 1)
        
        for location, data in comparative_data.items():
            if location != 'Canada':
                population = data.get('population', 0)
                percentage = (population / canada_pop) * 100 if canada_pop > 0 else 0
                print(f"  • {location}: {percentage:.2f}% of Canada's population")


async def main():
    """Run demographic analysis examples."""
    # Real-world case study
    await saugeen_shores_case_study()
    
    # Comparative analysis
    await comparative_analysis_example()
    
    print(f"\n🎉 Demographic Analysis Examples Complete!")
    print("💡 These examples show practical patterns for municipal and regional analysis")
    print("   Adapt coordinates and product IDs for your specific research needs")


if __name__ == "__main__":
    asyncio.run(main())
