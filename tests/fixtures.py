"""
Simple test fixtures for Statistics Canada package.
Uses fixture data first, then falls back to files in tests/data/ if needed.
"""

import json
import asyncio
from pathlib import Path
import pytest
from statscan.wds.client import Client


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def wds_client():
    """Create a WDS client for testing.""" 
    return Client()


@pytest.fixture(scope="session") 
def sample_code_sets():
    """Sample code sets data for testing."""
    return {
        "status": "SUCCESS",
        "object": {
            "scalar": [
                {"value": 0, "desc_en": "units", "desc_fr": "unités"},
                {"value": 1, "desc_en": "tens", "desc_fr": "dizaines"}
            ],
            "frequency": [
                {"value": 1, "desc_en": "Daily", "desc_fr": "Quotidienne"},
                {"value": 12, "desc_en": "Annual", "desc_fr": "Annuelle"}
            ]
        }
    }


@pytest.fixture(scope="session")
def sample_cube_metadata():
    """Sample cube metadata for testing."""
    return {
        "status": "SUCCESS", 
        "object": {
            "productId": 98100001,
            "cansimId": "98-10-0001-01",
            "cubeTitleEn": "Population and dwelling counts",
            "cubeTitleFr": "Chiffres de population et des logements",
            "cubeStartDate": "2021-01-01",
            "cubeEndDate": "2021-01-01",
            "dimension": [
                {
                    "dimensionPositionId": 1,
                    "dimensionNameEn": "Geography",
                    "dimensionNameFr": "Géographie"
                }
            ]
        }
    }


@pytest.fixture(scope="session")
def sample_cubes_list():
    """Sample cubes list for testing.""" 
    return [
        {
            "productId": 98100001,
            "cansimId": "98-10-0001-01", 
            "cubeTitleEn": "Population and dwelling counts",
            "cubeTitleFr": "Chiffres de population et des logements"
        },
        {
            "productId": 13100781,
            "cansimId": "13-10-0781-01",
            "cubeTitleEn": "Merchandise exports and imports, customs-based, by North American Product Classification System (NAPCS)",
            "cubeTitleFr": "Exportations et importations de marchandises, selon les douanes, par Système de classification des produits de l'Amérique du Nord (SCPAN)"
        }
    ]


def load_test_data(filename: str) -> dict | list:
    """
    Load test data from tests/data/ directory.
    
    Args:
        filename: Name of file in tests/data/ (e.g., 'wds/codes_data.json')
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = TEST_DATA_DIR / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"Test data file not found: {file_path}")
        
    with open(file_path, 'r') as f:
        return json.load(f)


@pytest.fixture(scope="session")
def wds_code_sets_data():
    """Load WDS code sets data fixture."""
    try:
        return load_test_data("wds/codes_data.json")
    except FileNotFoundError:
        pytest.skip("WDS code sets fixture not available")


@pytest.fixture(scope="session")
def wds_cubes_list_data():
    """Load WDS cubes list data fixture."""
    try:
        return load_test_data("wds/cubes_list_data.json")
    except FileNotFoundError:
        pytest.skip("WDS cubes list fixture not available")


@pytest.fixture(scope="session") 
def wds_cube_metadata_data():
    """Load WDS cube metadata fixture."""
    try:
        return load_test_data("wds/cube_metadata_data.json")
    except FileNotFoundError:
        pytest.skip("WDS cube metadata fixture not available")


@pytest.fixture(scope="session")
def wds_series_data():
    """Load WDS series data fixture."""
    try:
        return load_test_data("wds/series_data.json")
    except FileNotFoundError:
        pytest.skip("WDS series data fixture not available")


@pytest.fixture(scope="session")
def sdmx_minimal_data():
    """Load SDMX minimal data fixture."""
    try:
        return load_test_data("sdmx/minimal_data.json")
    except FileNotFoundError:
        pytest.skip("SDMX minimal data fixture not available")


def get_test_data_or_fixture(filename: str, fixture_data=None):
    """
    Get test data from fixture first, then fall back to file.
    
    Args:
        filename: File to load from tests/data/ if fixture not available
        fixture_data: Fixture data to use if available
        
    Returns:
        tuple: (data, source) where source is 'fixture' or 'file'
    """
    if fixture_data is not None:
        return fixture_data, 'fixture'
        
    try:
        file_data = load_test_data(filename)
        return file_data, 'file'
    except FileNotFoundError:
        raise Exception(f"No fixture data provided and no file found: {filename}")
