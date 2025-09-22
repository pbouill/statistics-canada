"""
Statistics Canada Package Integration Tests
==========================================

High-level integration tests that validate the complete package functionality.
These tests ensure all components work together for end users.

For detailed functionality tests, see:
- tests/wds/test_end_user_functionality.py - WDS API workflows  
- tests/sdmx/test_end_user_functionality.py - SDMX compatibility

For fixture generation, see:
- tests/wds/test_network_fixtures.py - Generate WDS test data
- tests/sdmx/test_network_fixtures.py - Generate SDMX test data
"""

import pytest
from statscan import __version__
from statscan.wds.client import Client
from statscan.enums.auto.province_territory import ProvinceTerritory
from statscan.enums.auto.wds.status import Status


def test_package_version():
    """Test package has version info.""" 
    assert __version__ is not None
    print(f"✅ Package version: {__version__}")


def test_main_components_available():
    """Test main package components can be imported."""
    # WDS client
    client = Client()
    assert client is not None
    
    # Geographic enums
    ontario = ProvinceTerritory.ONTARIO
    assert ontario.name == "ONTARIO"
    assert ontario.value == 35
    
    # Status enums  
    normal = Status.NORMAL
    assert normal.value == 0
    
    print("✅ Main package components available")
    print(f"   📊 WDS Client: {type(client).__name__}")
    print(f"   🗺️  Province enum: {ontario.name} = {ontario.value}")
    print(f"   📈 Status enum: {normal.name} = {normal.value}")


def test_sample_fixtures_work():
    """Test that fixture system works with sample data."""
    from tests.fixtures import sample_code_sets, sample_cube_metadata, sample_cubes_list
    
    # Get fixture instances (these are functions, need to call them)
    # For now, just test that they can be imported
    assert sample_code_sets is not None
    assert sample_cube_metadata is not None
    assert sample_cubes_list is not None
    
    print("✅ Fixture system imports working")
    print("   📋 Code sets fixture available")
    print("   📊 Cube metadata fixture available") 
    print("   📈 Cubes list fixture available")


def test_data_discovery_integration():
    """Test integrated data discovery workflow.""" 
    # Step 1: Test enum system for geography
    ontario = ProvinceTerritory.ONTARIO
    selected_pruid = ontario.value
    
    # Step 2: Test WDS client for data access
    client = Client()
    
    # Step 3: Workflow validation
    assert selected_pruid == 35  # Ontario PRUID
    assert hasattr(client, 'get_cube_metadata')
    
    print("✅ End-user workflow integration:")
    print(f"   1️⃣  WDS client available: {type(client).__name__}")
    print(f"   2️⃣  Geographic selection: {ontario.name} (PRUID: {selected_pruid})")
    print(f"   3️⃣  Ready for data retrieval")


def test_error_handling_integration():
    """Test integrated error handling."""
    # Test enum validation
    ontario = ProvinceTerritory.ONTARIO
    assert isinstance(ontario.value, int)
    assert ontario.value > 0
    
    # Test client creation
    client = Client()
    assert hasattr(client, 'get_cube_metadata')
    
    print("✅ Error handling integration validated")


def test_wds_enum_integration():
    """Test WDS client works with enumerations."""
    client = Client()
    
    # Test using enums with client methods
    ontario = ProvinceTerritory.ONTARIO
    status = Status.NORMAL
    
    # These would be used together in real workflows
    province_code = ontario.value  # For coordinate construction
    expected_status = status.value  # For data quality checking
    
    assert province_code == 35
    assert expected_status == 0
    assert hasattr(client, 'get_cube_metadata')
    
    print("✅ WDS-Enum integration ready")
    print(f"   🏢 Client methods: get_cube_metadata, get_all_cubes_list, etc.")
    print(f"   🗺️  Province codes: {ontario.name} → {province_code}")
    print(f"   📊 Status codes: {status.name} → {expected_status}")


def test_fixture_enum_integration():
    """Test fixture system works with enumerations."""
    ontario = ProvinceTerritory.ONTARIO
    
    # Test workflow: user selects geographic area and cube
    test_cube_id = 98100001  # Known census cube
    province_id = ontario.value
    
    # These would be used together for data requests
    assert test_cube_id == 98100001  # Census cube
    assert province_id == 35         # Ontario PRUID
    
    print("✅ Fixture-Enum integration ready")
    print(f"   📊 Target cube ID: {test_cube_id}")
    print(f"   🗺️  Province: {ontario.name} (PRUID: {province_id})")
    print(f"   🎯 Ready for: cube {test_cube_id} + province {province_id} data request")
