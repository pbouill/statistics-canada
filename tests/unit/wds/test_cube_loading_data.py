#!/usr/bin/env python3
"""Test cube metadata loading with fixed models."""

import json
from pathlib import Path
from statscan.wds.models.cube import Cube

def test_cube_from_api_response():
    """Test loading cube metadata from real WDS API response."""
    # Load the raw API response data
    test_data_path = Path(__file__).parent.parent.parent / "data" / "raw_cube_response.json"
    with open(test_data_path, 'r') as f:
        response_data = json.load(f)
    
    # Extract cube object from response
    cube_data = response_data[0]["object"]
    
    # Test cube loading
    cube = Cube.model_validate(cube_data)
    
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
    
    print(f"   Corrections: {len(cube.corrections) if cube.corrections else 0}")
    
    # Assert cube was created successfully (test validation)
    assert cube is not None
    assert cube.cubeTitleEn  # Fixed: use correct attribute name
    print("   ✅ Cube loaded and validated successfully")

if __name__ == "__main__":
    cube = test_cube_from_api_response()
    
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
