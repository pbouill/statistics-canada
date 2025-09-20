#!/usr/bin/env python3
"""Test cube metadata loading with fixed models."""

import json
from pathlib import Path
import pytest
from statscan.wds.models.cube import Cube

def test_cube_from_api_response():
    """Test loading cube metadata from real WDS API response."""
    # Load the raw API response data
    test_data_path = Path(__file__).parent / "data" / "raw_cube_response.json"
    with open(test_data_path, 'r') as f:
        response_data = json.load(f)
    
    # Extract cube object from response
    cube_data = response_data[0]["object"]
    
    # Test cube loading - this should not raise any exceptions
    cube = Cube.model_validate(cube_data)
    
    # Validate the cube was loaded correctly
    assert cube is not None, "Cube should be created successfully"
    assert isinstance(cube, Cube), "Should be a Cube instance"
    assert cube.cubeTitleEn, "Cube should have an English title"
    assert cube.productId > 0, "Cube should have a valid product ID"
    
    # Optional: Print information for debugging (only in verbose mode)
    print(f"✅ Cube loaded successfully!")
    print(f"   Title: {cube.cubeTitleEn}")
    print(f"   Product ID: {cube.productId}")
    print(f"   Dimensions: {len(cube.dimensions) if cube.dimensions else 0}")
    
    if cube.dimensions:
        for i, dim in enumerate(cube.dimensions):
            print(f"   Dim {i+1}: {dim.dimensionNameEn} ({len(dim.member)} members)")
            # Show sample members
            if dim.member:
                sample_members = dim.member[:3]  # First 3 members
                for member in sample_members:
                    print(f"     - {member.memberNameEn}")
                if len(dim.member) > 3:
                    print(f"     ... and {len(dim.member) - 3} more")
    
    print(f"   Corrections: {len(cube.correction) if cube.correction else 0}")
    
    # Test function should not return anything for pytest compliance

@pytest.fixture
def sample_cube():
    """Fixture to provide a loaded cube for testing."""
    test_data_path = Path(__file__).parent / "data" / "raw_cube_response.json"
    with open(test_data_path, 'r') as f:
        response_data = json.load(f)
    
    cube_data = response_data[0]["object"]
    return Cube.model_validate(cube_data)

def test_cube_dimensions_exist(sample_cube):
    """Test that cube dimensions are properly loaded."""
    if sample_cube.dimensions:
        assert len(sample_cube.dimensions) > 0, "Cube should have dimensions"
        for dim in sample_cube.dimensions:
            assert dim.dimensionNameEn, "Each dimension should have an English name"
            assert dim.member, "Each dimension should have members"

def test_cube_geographic_dimension(sample_cube):
    """Test that geographic dimension can be found and contains members."""
    if not sample_cube.dimensions:
        pytest.skip("No dimensions available in test cube")
    
    geo_dim = None
    for dim in sample_cube.dimensions:
        if "geographic" in dim.dimensionNameEn.lower():
            geo_dim = dim
            break
    
    if geo_dim:
        assert len(geo_dim.member) > 0, "Geographic dimension should have members"
        # Test that members have required attributes
        for member in geo_dim.member[:5]:  # Test first 5 members
            assert member.memberNameEn, "Member should have English name"
            assert member.memberId, "Member should have ID"

def demonstrate_cube_analysis():
    """Standalone function to demonstrate cube analysis (not a test)."""
    # Load the test data
    test_data_path = Path(__file__).parent / "data" / "raw_cube_response.json"
    with open(test_data_path, 'r') as f:
        response_data = json.load(f)
    
    cube_data = response_data[0]["object"]
    cube = Cube.model_validate(cube_data)
    
    # Look for Saugeen Shores specifically
    print("\n🔍 Searching for Saugeen Shores in geographic dimension...")
    geo_dim = None
    for dim in cube.dimensions or []:
        if "geographic" in dim.dimensionNameEn.lower():
            geo_dim = dim
            break
    
    if geo_dim:
        saugeen_members = [m for m in geo_dim.member if "saugeen" in m.memberNameEn.lower()]
        if saugeen_members:
            print(f"   Found {len(saugeen_members)} Saugeen entries:")
            for member in saugeen_members:
                print(f"   - ID {member.memberId}: {member.memberNameEn}")
                print(f"     Classification: {member.classificationCode}, Geo Level: {member.geoLevel}")
        else:
            print("   ❌ No Saugeen Shores found in this cube")
            print(f"   Available locations (first 10):")
            for member in geo_dim.member[:10]:
                print(f"   - {member.memberNameEn}")
    else:
        print("   ❌ No geographic dimension found")
    
    return cube

if __name__ == "__main__":
    # Run the demonstration when script is executed directly
    demonstrate_cube_analysis()
