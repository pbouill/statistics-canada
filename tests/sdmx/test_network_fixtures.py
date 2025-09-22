"""
SDMX Network Tests - Fixture Generation
======================================

This module generates test fixtures for SDMX functionality.
SDMX is a secondary priority compared to WDS API.

Tests here:
1. Use existing SDMX data if available
2. Generate minimal fixtures for SDMX parsing tests
3. Support legacy SDMX functionality without extensive network calls

Note: SDMX is mainly for compatibility - WDS API is the primary focus.
"""

import pytest
import json
from pathlib import Path
from statscan.sdmx.response import SDMXResponse
from tests.fixtures import load_test_data


class TestSDMXFixtureGeneration:
    """Generate minimal SDMX fixtures from existing data."""
    
    def save_fixture(self, filename: str, data: dict) -> None:
        """Save SDMX test data as JSON fixture."""
        fixture_path = Path(__file__).parent.parent / "data" / "sdmx" / filename
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(fixture_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"💾 Saved SDMX fixture: {fixture_path}")
    
    def test_create_minimal_sdmx_fixture(self):
        """Create minimal SDMX response fixture for testing."""
        # Create minimal valid SDMX structure
        minimal_sdmx = {
            "meta": {
                "name": "Test SDMX Response",
                "version": "1.0",
                "source": "test_fixture"
            },
            "data": {
                "structure": {
                    "dimensions": [],
                    "attributes": []
                },
                "dataSets": []
            },
            "_test_metadata": {
                "source": "minimal_fixture",
                "description": "Basic SDMX structure for parsing tests",
                "note": "SDMX is secondary priority - WDS API is primary"
            }
        }
        
        self.save_fixture("minimal_response.json", minimal_sdmx)
        print("✅ Created minimal SDMX fixture")
    
    def test_use_existing_sdmx_data(self):
        """Use existing SDMX data as fixture if available."""
        try:
            # Try to load existing SDMX data from main test data
            existing_data = load_test_data("raw_cube_response.json")
            
            # Handle different data types (list or dict)
            if isinstance(existing_data, dict):
                fixture_data = {
                    **existing_data,
                    "_test_metadata": {
                        "source": "existing_data",
                        "description": "Real SDMX response data for parsing tests"
                    }
                }
            else:
                # Wrap list data in a structure
                fixture_data = {
                    "data": existing_data,
                    "_test_metadata": {
                        "source": "existing_data",
                        "description": "Real SDMX response data for parsing tests",
                        "note": "Original data was list format"
                    }
                }
            
            self.save_fixture("real_response.json", fixture_data)
            print("✅ Created SDMX fixture from existing data")
            
        except FileNotFoundError:
            print("ℹ️  No existing SDMX data found - using minimal fixture only")


class TestSDMXFixtureValidation:
    """Validate SDMX fixtures are usable."""
    
    def test_minimal_fixture_exists(self):
        """Verify minimal SDMX fixture is valid."""
        try:
            data = load_test_data("sdmx/minimal_response.json")
            assert "meta" in data
            assert "data" in data
            print("✅ Minimal SDMX fixture is valid")
        except FileNotFoundError:
            pytest.skip("Minimal SDMX fixture not generated yet")
    
    def test_real_fixture_if_available(self):
        """Test real SDMX fixture if it exists."""
        try:
            data = load_test_data("sdmx/real_response.json")
            assert data is not None
            print("✅ Real SDMX fixture is available and valid")
        except FileNotFoundError:
            print("ℹ️  Real SDMX fixture not available - minimal fixture sufficient")
