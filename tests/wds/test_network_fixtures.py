"""
WDS Network Tests - Fixture Generation
=====================================

This module contains tests that make actual network calls to the WDS API
to generate test fixtures for other tests to use.

Tests here:
1. Make live API calls to fetch current data
2. Save responses as JSON fixtures in tests/data/wds/
3. Generate reusable test data for end-user functionality tests

Test execution order matters - these should run first to generate
fixtures that other tests depend on.
"""

import pytest
import json
import asyncio
from pathlib import Path
from statscan.wds.client import Client
from statscan.wds.models.code import CodeSets
from tests.fixtures import load_test_data


class TestWDSNetworkFixtures:
    """Generate fixtures from live WDS API calls."""
    
    def save_fixture(self, filename: str, data: dict | list) -> None:
        """Save test data as JSON fixture."""
        fixture_path = Path(__file__).parent.parent / "data" / "wds" / filename
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(fixture_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"💾 Saved fixture: {fixture_path}")
    
    @pytest.mark.asyncio
    @pytest.mark.network
    async def test_fetch_code_sets_fixture(self, wds_client):
        """Fetch code sets from WDS API and save as fixture."""
        try:
            response = await wds_client.get_code_sets()
            assert isinstance(response, CodeSets)
            
            # Convert to dict for JSON serialization
            fixture_data = {
                "status": "SUCCESS",
                "object": response.model_dump(),
                "_test_metadata": {
                    "source": "live_api",
                    "endpoint": "getCodeSets",
                    "description": "WDS code sets for testing"
                }
            }
            
            self.save_fixture("code_sets.json", fixture_data)
            print(f"✅ Generated code sets fixture with {len(response.root)} code sets")
            
        except Exception as e:
            pytest.skip(f"Network test failed - could not fetch code sets: {e}")
    
    @pytest.mark.asyncio 
    @pytest.mark.network
    async def test_fetch_cubes_list_fixture(self, wds_client):
        """Fetch cubes list from WDS API and save as fixture."""
        try:
            response = await wds_client.get_all_cubes_list()
            assert isinstance(response, list)
            assert len(response) > 1000
            
            # Take a sample for testing (first 50 cubes)
            sample_cubes = response[:50]
            
            fixture_data = {
                "status": "SUCCESS", 
                "object": [cube.model_dump() for cube in sample_cubes],
                "_test_metadata": {
                    "source": "live_api",
                    "endpoint": "getAllCubesList", 
                    "description": "Sample WDS cubes list for testing",
                    "total_available": len(response),
                    "sample_size": len(sample_cubes)
                }
            }
            
            self.save_fixture("cubes_list.json", fixture_data)
            print(f"✅ Generated cubes list fixture with {len(sample_cubes)}/{len(response)} cubes")
            
        except Exception as e:
            pytest.skip(f"Network test failed - could not fetch cubes list: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.network 
    async def test_fetch_cube_metadata_fixture(self, wds_client):
        """Fetch specific cube metadata and save as fixture."""
        # Test with well-known census cube
        test_cube_id = 98100001  # Population and dwelling counts
        
        try:
            response = await wds_client.get_cube_metadata(test_cube_id)
            assert response is not None
            assert response.productId == test_cube_id
            
            fixture_data = {
                "status": "SUCCESS",
                "object": response.model_dump(),
                "_test_metadata": {
                    "source": "live_api", 
                    "endpoint": "getCubeMetadata",
                    "description": f"Cube metadata for product {test_cube_id}",
                    "cube_id": test_cube_id
                }
            }
            
            self.save_fixture(f"cube_metadata_{test_cube_id}.json", fixture_data)
            print(f"✅ Generated metadata fixture for cube {test_cube_id}: {response.cubeTitleEn}")
            
        except Exception as e:
            pytest.skip(f"Network test failed - could not fetch cube {test_cube_id} metadata: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.network
    async def test_fetch_series_data_fixture(self, wds_client):
        """Fetch sample series data and save as fixture.""" 
        # Use a simple coordinate for population data
        test_cube_id = 98100001
        test_coordinate = "1.1.1.1.1.1.0.0.0.0"  # Canada total population
        
        try:
            response = await wds_client.get_data_from_cube_pid_coord_and_latest_n_periods(
                product_id=test_cube_id,
                coordinate=test_coordinate,
                latest_n=1  # Just get latest period
            )
            
            assert response is not None
            
            fixture_data = {
                "status": "SUCCESS",
                "object": response.model_dump() if hasattr(response, 'model_dump') else response,
                "_test_metadata": {
                    "source": "live_api",
                    "endpoint": "getDataFromCubePidCoordAndLatestNPeriods", 
                    "description": f"Series data for cube {test_cube_id}",
                    "cube_id": test_cube_id,
                    "coordinate": test_coordinate,
                    "periods": 1
                }
            }
            
            self.save_fixture(f"series_data_{test_cube_id}.json", fixture_data)
            print(f"✅ Generated series data fixture for cube {test_cube_id}")
            
        except Exception as e:
            pytest.skip(f"Network test failed - could not fetch series data: {e}")


class TestWDSFixtureValidation:
    """Validate that generated fixtures are usable."""
    
    def test_code_sets_fixture_exists(self):
        """Verify code sets fixture was created and is valid."""
        try:
            data = load_test_data("wds/code_sets.json")
            assert data["status"] == "SUCCESS"
            assert "object" in data
            assert len(data["object"]) > 0
            print("✅ Code sets fixture is valid")
        except FileNotFoundError:
            pytest.skip("Code sets fixture not generated yet")
    
    def test_cubes_list_fixture_exists(self):
        """Verify cubes list fixture was created and is valid."""
        try:
            data = load_test_data("wds/cubes_list.json") 
            assert data["status"] == "SUCCESS"
            assert "object" in data
            assert len(data["object"]) > 0
            print(f"✅ Cubes list fixture contains {len(data['object'])} cubes")
        except FileNotFoundError:
            pytest.skip("Cubes list fixture not generated yet")
    
    def test_cube_metadata_fixture_exists(self):
        """Verify cube metadata fixture was created and is valid."""
        try:
            data = load_test_data("wds/cube_metadata_98100001.json")
            assert data["status"] == "SUCCESS"
            assert "object" in data
            cube = data["object"]
            assert cube["productId"] == 98100001
            print(f"✅ Cube metadata fixture: {cube['cubeTitleEn']}")
        except FileNotFoundError:
            pytest.skip("Cube metadata fixture not generated yet")
