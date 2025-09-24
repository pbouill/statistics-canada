#!/usr/bin/env python3
"""
WDS Client Overview - Complete functionality demonstration

This example shows all the capabilities of the main WDS Client class.
"""

import asyncio
import pandas as pd
from statscan.wds.client import Client


async def demonstrate_client_capabilities():
    """Demonstrate the complete Client functionality."""
    
    print("🏆 WDS CLIENT OVERVIEW")
    print("=" * 50)
    print()
    print("The main Client class provides ALL WDS functionality:")
    print("• Basic WDS API endpoints")  
    print("• Geographic entity management")
    print("• Population queries")
    print("• Location search")
    print("• Data retrieval in multiple formats")
    print()
    
    # Initialize single client for everything
    client = Client()
    
    # 1. Basic population lookup
    print("1️⃣ SIMPLE POPULATION LOOKUP")
    print("-" * 30)
    
    try:
        population = await client.get_population(2314)
        print(f"✅ Saugeen Shores (Member ID 2314): {population:,} people")
        
        # Try name-based lookup (requires metadata)
        population_by_name = await client.get_population("Canada")  
        if population_by_name:
            print(f"✅ Canada: {population_by_name:,} people")
        else:
            print("⚠️  Name-based lookup requires cube metadata (slower)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Location search
    print(f"\n2️⃣ LOCATION SEARCH")
    print("-" * 20)
    
    try:
        # Search doesn't work yet because it needs metadata, but shows the API
        results = await client.search_locations("saugeen") 
        if results:
            print(f"✅ Found {len(results)} locations:")
            for member_id, name in results[:5]:
                print(f"   • {member_id}: {name}")
        else:
            print("⚠️  Search requires cube metadata loading (not implemented in this demo)")
            
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    # 3. Data in different formats  
    print(f"\n3️⃣ DATA IN MULTIPLE FORMATS")
    print("-" * 30)
    
    member_id = 2314  # Saugeen Shores
    
    try:
        # Population only
        pop = await client.get_location_data(member_id, format="population")
        print(f"✅ Population format: {pop:,}")
        
        # Geographic entity
        entity = await client.get_location_data(member_id, format="entity")
        print(f"✅ Entity format: {entity}")
        
        # DataFrame
        df = await client.get_location_data(member_id, format="dataframe", periods=3)
        if df is not None and len(df) > 0:
            print(f"✅ DataFrame format: {df.shape[0]} rows × {df.shape[1]} columns")
            print(f"   Sample: {df['value'].iloc[0]} population")
            print(f"   Quality: {df['quality_info'].iloc[0]}")
        
        # Array
        array = await client.get_location_data(member_id, format="array", periods=5)
        if array is not None:
            print(f"✅ Array format: {len(array)} values")
            
    except Exception as e:
        print(f"❌ Format error: {e}")
    
    print(f"\n🎯 BENEFITS OF UNIFIED CLIENT APPROACH:")
    print("✅ Single import and client class")
    print("✅ Consistent API across all data types")  
    print("✅ Integrated cube management")
    print("✅ No confusion about which client to use")
    print("✅ Better performance (shared connections & caching)")
    print("✅ Simpler testing and debugging")





if __name__ == "__main__":
    asyncio.run(demonstrate_client_capabilities())
