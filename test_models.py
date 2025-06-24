#!/usr/bin/env python3
"""
Test script to verify the Pydantic models work with sample Stats Canada API data.
"""

import json
from pathlib import Path
from statscan.data import parse_sdmx_response, extract_observations

def test_data_response():
    """Test parsing a data response."""
    data_file = Path("data/A5.2021A000235.1..1.json")
    if data_file.exists():
        print("Testing data response parsing...")
        with open(data_file, 'r') as f:
            json_data = json.load(f)
        
        response = parse_sdmx_response(json_data)
        print(f"Parsed as: {type(response).__name__}")
        print(f"Meta ID: {response.meta.id}")
        print(f"Schema URL: {response.meta.schema_url}")
        print(f"Number of datasets: {len(response.data.data_sets)}")
        
        # Extract some observations
        if response.data.data_sets and response.data.data_sets[0].series:
            observations = extract_observations(response.data.data_sets[0].series)
            print(f"Total observations: {len(observations)}")
            if observations:
                print(f"Sample observation: {observations[0]}")
        print("✓ Data response test passed\n")
    else:
        print("⚠ Data file not found, skipping data response test\n")

def test_structure_response():
    """Test parsing a structure/metadata response."""
    metadata_file = Path("data/df_pr_metadata.json")
    if metadata_file.exists():
        print("Testing structure response parsing...")
        with open(metadata_file, 'r') as f:
            json_data = json.load(f)
        
        response = parse_sdmx_response(json_data)
        print(f"Parsed as: {type(response).__name__}")
        print(f"Meta ID: {response.meta.id}")
        
        if hasattr(response.data, 'dataflows') and response.data.dataflows:
            print(f"Number of dataflows: {len(response.data.dataflows)}")
            print(f"First dataflow: {response.data.dataflows[0].name}")
        
        if hasattr(response.data, 'codelists') and response.data.codelists:
            print(f"Number of codelists: {len(response.data.codelists)}")
            print(f"First codelist: {response.data.codelists[0].name}")
        
        print("✓ Structure response test passed\n")
    else:
        print("⚠ Metadata file not found, skipping structure response test\n")

def test_dataflows_response():
    """Test parsing a dataflows response."""
    dataflows_file = Path("data/dataflows.json")
    if dataflows_file.exists():
        print("Testing dataflows response parsing...")
        with open(dataflows_file, 'r') as f:
            json_data = json.load(f)
        
        response = parse_sdmx_response(json_data)
        print(f"Parsed as: {type(response).__name__}")
        print(f"Number of references: {len(response.references)}")
        
        # Show a few dataflow names
        dataflow_names = [df.name for df in list(response.references.values())[:3]]
        print(f"Sample dataflows: {dataflow_names}")
        print("✓ Dataflows response test passed\n")
    else:
        print("⚠ Dataflows file not found, skipping dataflows response test\n")

if __name__ == "__main__":
    print("Testing Stats Canada API Pydantic models...\n")
    
    try:
        test_data_response()
        test_structure_response() 
        test_dataflows_response()
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
