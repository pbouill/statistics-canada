"""
Enhanced Statistics Canada Package Usage Examples

This file demonstrates the new convenience functions, enhanced response handlers,
and improved data extraction capabilities.
"""

import asyncio
from statscan.dguid import DGUID
from statscan.enums.auto.census_subdivision import CensusSubdivision
from statscan.enums.auto.province_territory import ProvinceTerritory
from statscan.enums.enhanced_stats_filter import (
    Gender, CensusProfileCharacteristic, StatisticType, 
    EnhancedStatsFilter, CommonFilters
)


async def basic_enhanced_usage():
    """Demonstrate basic enhanced functionality."""
    print("=== Basic Enhanced Usage ===")
    
    # Create DGUID for a municipality
    dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    print(f"DGUID: {dguid}")
    
    # Get enhanced response object instead of raw JSON
    response = await dguid.get_response(timeout=15)
    print(f"Total series: {len(response.series_info)}")
    print(f"Available dimensions: {list(response.dimensions.keys())}")
    
    # Get data as enhanced DataFrame
    df = await dguid.get_dataframe(timeout=15)
    print(f"DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")


async def filtering_with_enums():
    """Demonstrate filtering using enhanced enums."""
    print("\n=== Filtering with Enhanced Enums ===")
    
    dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    
    # Get DataFrame and filter using enum values
    df = await dguid.get_dataframe(timeout=15)
    
    # Filter by specific characteristics using enums
    population_data = df.filter_by_enum(
        gender=Gender.TOTAL_GENDER,
        characteristic=CensusProfileCharacteristic.POPULATION_COUNT
    )
    print(f"Population data shape: {population_data.shape}")
    
    # Filter by gender
    male_data = df.filter_by_gender("Male")
    female_data = df.filter_by_gender("Female")
    print(f"Male data: {len(male_data)} records")
    print(f"Female data: {len(female_data)} records")


async def data_discovery():
    """Demonstrate data discovery capabilities."""
    print("\n=== Data Discovery ===")
    
    dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    
    # Discover what data is available
    description = await dguid.describe_data(timeout=15)
    print("Available data description:")
    print(description)
    
    # Get detailed summary
    summary = await dguid.get_available_dimensions(timeout=15)
    print(f"\nDetailed summary:")
    print(f"Total series: {summary.get('total_series', 0)}")
    
    if 'available_values' in summary:
        for dim_name, values in summary['available_values'].items():
            print(f"{dim_name}: {len(values)} values")
            print(f"  First few: {', '.join(values[:3])}")


async def convenience_data_methods():
    """Demonstrate convenience methods for specific data types."""
    print("\n=== Convenience Data Methods ===")
    
    dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    
    # Get specific types of data using convenience methods
    population_data = await dguid.get_population_data(timeout=15)
    print(f"Population data: {len(population_data)} records")
    
    age_data = await dguid.get_age_demographics(timeout=15)
    print(f"Age demographics: {len(age_data)} records")
    
    household_data = await dguid.get_household_statistics(timeout=15)
    print(f"Household statistics: {len(household_data)} records")
    
    # Use DataFrame convenience methods
    df = await dguid.get_dataframe(timeout=15)
    
    income_data = df.get_income_data()
    print(f"Income-related data: {len(income_data)} records")
    
    education_data = df.get_education_data()
    print(f"Education-related data: {len(education_data)} records")
    
    employment_data = df.get_employment_data()
    print(f"Employment-related data: {len(employment_data)} records")


async def enhanced_filtering():
    """Demonstrate enhanced filtering with response handlers."""
    print("\n=== Enhanced Filtering ===")
    
    dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    response = await dguid.get_response(timeout=15)
    
    # Filter using enhanced filter objects
    enhanced_filter = EnhancedStatsFilter(
        gender=Gender.TOTAL_GENDER,
        census_profile_characteristic=CensusProfileCharacteristic.POPULATION_COUNT,
        statistic_type=StatisticType.COUNT
    )
    
    filtered_series = response.filter_by_enhanced_filter(enhanced_filter)
    print(f"Filtered series: {len(filtered_series)}")
    
    for series in filtered_series[:3]:  # Show first 3
        print(f"  {series.dimension_summary}")
    
    # Use common filters
    pop_filter = CommonFilters.population_total()
    pop_series = response.filter_by_enhanced_filter(pop_filter)
    print(f"Population total series: {len(pop_series)}")
    
    # Get characteristics by category
    characteristics_by_category = response.get_characteristics_by_category()
    for category, chars in characteristics_by_category.items():
        print(f"{category}: {len(chars)} characteristics")


async def advanced_dataframe_analysis():
    """Demonstrate advanced DataFrame analysis capabilities."""
    print("\n=== Advanced DataFrame Analysis ===")
    
    dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    df = await dguid.get_dataframe(timeout=15)
    
    # Get summary statistics
    stats = df.summary_stats()
    print(f"Dataset summary:")
    print(f"  Shape: {stats['shape']}")
    print(f"  Numeric columns: {len(stats['numeric_columns'])}")
    
    # Compare by gender
    gender_comparison = df.compare_by_gender()
    if not gender_comparison.empty:
        print(f"\nGender comparison shape: {gender_comparison.shape}")
        print(f"Columns: {list(gender_comparison.columns)}")
    
    # Get top characteristics by value
    top_chars = df.get_top_characteristics(n=5, by_value=True)
    print(f"\nTop 5 characteristics by value:")
    if not top_chars.empty and 'value' in top_chars.columns:
        char_col = next((col for col in top_chars.columns if 'characteristic' in col.lower()), None)
        if char_col:
            for _, row in top_chars.iterrows():
                print(f"  {row[char_col]}: {row['value']}")
    
    # Get latest values only
    latest = df.get_latest_values()
    print(f"\nLatest values dataset: {len(latest)} records")


async def compare_geographic_areas():
    """Demonstrate comparing data across different geographic areas."""
    print("\n=== Geographic Comparison ===")
    
    # Compare data between different municipalities
    dguid1 = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    dguid2 = DGUID(geocode=CensusSubdivision.ONT_TORONTO)
    
    # Get population data for both
    pop1 = await dguid1.get_population_data(timeout=15)
    pop2 = await dguid2.get_population_data(timeout=15)
    
    print(f"Saugeen Shores population data: {len(pop1)} records")
    print(f"Toronto population data: {len(pop2)} records")
    
    # You could combine and compare the data here
    # This demonstrates the framework for geographic comparison


async def working_with_common_filters():
    """Demonstrate using pre-built common filters."""
    print("\n=== Common Filters Usage ===")
    
    dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    response = await dguid.get_response(timeout=15)
    
    # Use pre-built common filters
    filters_to_test = [
        ("Total Population", CommonFilters.population_total()),
        ("Median Age", CommonFilters.median_age_total()),
        ("Median Household Income", CommonFilters.household_income_median()),
        ("Total Dwellings", CommonFilters.total_dwellings()),
    ]
    
    for name, filter_obj in filters_to_test:
        filtered_series = response.filter_by_enhanced_filter(filter_obj)
        print(f"{name}: {len(filtered_series)} series found")
        
        if filtered_series:
            # Get the latest value
            series = filtered_series[0]
            latest_value = series.observations.get(max(series.observations.keys()), [None])[0] if series.observations else None
            print(f"  Latest value: {latest_value}")


async def main():
    """Run all examples."""
    try:
        await basic_enhanced_usage()
        await filtering_with_enums()
        await data_discovery()
        await convenience_data_methods()
        await enhanced_filtering()
        await advanced_dataframe_analysis()
        await compare_geographic_areas()
        await working_with_common_filters()
        
        print("\n=== All examples completed successfully! ===")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())
