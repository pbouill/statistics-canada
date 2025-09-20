#!/usr/bin/env python3
"""
Statistics Canada WDS API - Basic Usage Examples

This example demonstrates the fundamental patterns for using the Statistics Canada
Web Data Service (WDS) API through the statscan package.

Key Concepts:
- WDS client initialization and basic API calls
- Product discovery and cube metadata retrieval  
- Simple data requests using coordinates
- Working with WDS enums and response parsing
"""

import asyncio
from statscan.wds.client import Client
from statscan.enums.auto.wds.product_id import ProductID


async def basic_api_usage():
    """Demonstrate basic WDS API patterns."""
    print("🚀 Statistics Canada WDS API - Basic Usage")
    print("=" * 50)
    
    # Initialize client
    client = Client()
    
    # 1. Discover available products
    print("\n📊 1. Product Discovery")
    print("-" * 30)
    
    # Get basic population cube metadata
    population_product = ProductID.POPULATION_AND_DWELLINGS_COUNTS_CANADA_PROVINCES_TERRITORIES_CENSUS_METROPOLITAN_AREAS_AND_CENSUS_AGGLOMERATIONS_INCLUDING_PARTS
    metadata = await client.get_cube_metadata(product_id=population_product.value)
    
    print(f"Product ID: {population_product.value}")
    print(f"Title: {metadata['object']['cubeTitleEn']}")
    print(f"Dimensions: {len(metadata['object']['dimension'])} dimensions")
    
    # 2. Simple coordinate-based data request
    print("\n📈 2. Basic Data Request")
    print("-" * 30)
    
    # Get Canada total population for 2021
    coordinates = "1.1.1.1.1.1.1.1.1.1"  # Canada, both sexes, total age, 2021
    periods = 1  # Latest period only
    
    data_response = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
        product_id=population_product.value,
        coordinate=coordinates,
        periods=periods
    )
    
    if data_response['status'] == 'SUCCESS':
        observations = data_response['object']
        if observations:
            latest_data = observations[0]
            print(f"Canada Population (2021): {latest_data['vectorDataPoint']:,}")
            print(f"Reference Date: {latest_data['refPer']}")
        else:
            print("No data returned for specified coordinates")
    else:
        print(f"API Error: {data_response.get('status', 'Unknown error')}")
    
    # 3. Explore cube structure
    print("\n🔍 3. Cube Structure Exploration")
    print("-" * 30)
    
    # Show dimension information
    dimensions = metadata['object']['dimension']
    for i, dim in enumerate(dimensions[:3]):  # Show first 3 dimensions
        print(f"Dimension {i+1}: {dim['dimensionNameEn']}")
        print(f"  Members: {len(dim['member'])} options")
        if dim['member']:
            print(f"  Example: {dim['member'][0]['memberNameEn']}")
        print()
    
    print(f"💡 This cube has {len(dimensions)} total dimensions")
    print("   Use coordinates to specify which data subset you want")
    

async def working_with_enums():
    """Demonstrate using WDS enums for type-safe API calls."""
    print("\n🎯 Working with WDS Enums")
    print("=" * 50)
    
    from statscan.enums.auto.wds.frequency import Frequency
    
    client = Client()
    
    # Use enums for better code maintainability
    print("📋 Available Product Categories:")
    
    # Show some census-related products
    census_products = [
        (ProductID.POPULATION_AND_DWELLINGS_COUNTS_CANADA_PROVINCES_TERRITORIES_CENSUS_METROPOLITAN_AREAS_AND_CENSUS_AGGLOMERATIONS_INCLUDING_PARTS, "Population & Dwellings"),
        (ProductID.AGE_AND_SEX_HIGHLIGHTS_CANADA_PROVINCES_AND_TERRITORIES_CENSUS_METROPOLITAN_AREAS_AND_CENSUS_AGGLOMERATIONS_INCLUDING_PARTS, "Age & Sex Demographics"),
        (ProductID.HOUSEHOLDS_AND_MARITAL_STATUS_HIGHLIGHTS_CANADA_PROVINCES_AND_TERRITORIES_CENSUS_METROPOLITAN_AREAS_AND_CENSUS_AGGLOMERATIONS_INCLUDING_PARTS, "Household & Marital Status")
    ]
    
    for product_enum, description in census_products:
        print(f"  • {description}")
        print(f"    Product ID: {product_enum.value}")
        print(f"    Enum Name: {product_enum.name}")
        print()
    
    # Demonstrate frequency enum usage
    print("📅 Data Frequencies Available:")
    frequency_examples = [
        Frequency.ANNUAL,
        Frequency.QUARTERLY, 
        Frequency.MONTHLY
    ]
    
    for freq in frequency_examples:
        print(f"  • {freq.name}: {freq.value}")


async def error_handling_patterns():
    """Show proper error handling for WDS API calls."""
    print("\n⚠️  Error Handling Best Practices")
    print("=" * 50)
    
    client = Client()
    
    try:
        # Example of handling invalid product ID
        print("Testing invalid product ID handling...")
        response = await client.get_cube_metadata(product_id=99999999)
        
        if response['status'] != 'SUCCESS':
            print(f"✅ Properly handled API error: {response['status']}")
        else:
            print("⚠️  Unexpected success with invalid product ID")
            
    except Exception as e:
        print(f"✅ Caught exception: {type(e).__name__}: {e}")
    
    try:
        # Example of handling invalid coordinates
        print("\nTesting invalid coordinate handling...")
        response = await client.get_data_from_cube_pid_coord_and_latest_n_periods(
            product_id=ProductID.POPULATION_AND_DWELLINGS_COUNTS_CANADA_PROVINCES_TERRITORIES_CENSUS_METROPOLITAN_AREAS_AND_CENSUS_AGGLOMERATIONS_INCLUDING_PARTS.value,
            coordinate="999.999.999",  # Invalid coordinate format
            periods=1
        )
        
        if response['status'] != 'SUCCESS':
            print(f"✅ Properly handled coordinate error: {response['status']}")
        
    except Exception as e:
        print(f"✅ Caught coordinate exception: {type(e).__name__}: {e}")
    
    print("\n💡 Key Error Handling Tips:")
    print("  • Always check response['status'] for 'SUCCESS'")
    print("  • Use try/catch for network and parsing errors")
    print("  • Validate coordinates before API calls")
    print("  • Handle empty result sets gracefully")


async def main():
    """Run all basic usage examples."""
    await basic_api_usage()
    await working_with_enums()
    await error_handling_patterns()
    
    print("\n🎉 Basic Usage Examples Complete!")
    print("Next steps: Try demographic_analysis.py for real-world use cases")


if __name__ == "__main__":
    asyncio.run(main())
