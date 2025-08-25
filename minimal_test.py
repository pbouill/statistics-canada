#!/usr/bin/env python3
"""
Minimal test for SDMX data retrieval.
"""
import asyncio
from statscan.dguid import DGUID
from statscan.enums.auto.census_subdivision import CensusSubdivision

async def main():
    print("Creating DGUID...")
    dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
    print(f"DGUID: {dguid}")
    
    print("Updating...")
    await dguid.update(timeout=30)
    
    print("Checking response...")
    response = dguid.sdmx_response
    print(f"Response: {response}")
    
    if response:
        print("Getting DataFrame...")
        df = response.dataframe
        print(f"Shape: {df.shape}")
        print(f"Raw data available: {response._raw_data is not None}")

if __name__ == "__main__":
    asyncio.run(main())
