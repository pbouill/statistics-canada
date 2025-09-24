"""
Pytest configuration and shared fixtures.

Imports both legacy fixtures (for compatibility) and new enhanced fixtures
that support raw response data and specialized data extraction.
"""

import pytest
from unittest.mock import patch


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--no-mock",
        action="store_true",
        default=False,
        help="Disable mocking and run network tests instead"
    )

from statscan.wds.client import Client as WDSClient
from statscan.wds.requests import WDSRequests, ResponseKeys
from statscan.wds.models.cube import Cube
from statscan.wds.models.code import CodeSets

from tests.data_store import WDSDataPaths, SESSION_DATA_SAVED_ATTR
from tests.wds.test_requests import TestCodeSets, TestCubesListLite, TestCubeMeta


TRACKED_TESTS = {
    TestCodeSets.test_get_codesets.__name__:  WDSDataPaths.CODESETS.name,
    TestCubesListLite.test_get_cubeslistlite.__name__: WDSDataPaths.CUBESLIST_LITE.name,
    TestCubeMeta.test_get_cubemetadata.__name__: WDSDataPaths.CUBEMETA.name,
}

def pytest_collection_modifyitems(config, items: list[pytest.Item]):
    """
    Modify test collection to prioritize network tests.
    This ensures network tests run first to generate fresh data.
    """
    # Separate network tests from others
    network_tests = []
    other_tests = []
    
    for item in items:
        if item.get_closest_marker("network"):
            network_tests.append(item)
        else:
            other_tests.append(item)
    
    # Reorder: network tests first, then others
    items[:] = network_tests + other_tests


def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """
    Hook that runs after each test stage (setup, call, teardown).
    We use it to check if API requests tests have failed and track successful data saves.
    """
    if call.when == "call":
        if data_path_name := TRACKED_TESTS.get(item.name):
            if not isinstance(sd := getattr(item.session, SESSION_DATA_SAVED_ATTR, None), dict):
                sd = {}
                setattr(item.session, SESSION_DATA_SAVED_ATTR, sd)
            sd[data_path_name] = (item.name, call.excinfo)


@pytest.fixture(scope="session")
def wds_client() -> WDSClient:
    """
    Provides a WDS client instance configured to use local test data
    instead of making actual web requests.
    """
    client = WDSClient()
    
    # # Override the client's HTTP methods to use local data
    # async def mock_get_codesets() -> CodeSets:
    #     data= WDSDataPaths.CODESETS.load()
    #     return WDSRequests.dict_to_model(data=data[ResponseKeys.OBJECT], model=CodeSets)
    #     # return CodeSets.model_validate(data)
    
    # async def mock_get_cubeslistlite():
    #     data = WDSDataPaths.CUBESLIST_LITE.load()
    #     cubes = [WDSRequests.dict_to_model(data=item[ResponseKeys.OBJECT], model=Cube) for item in data]
    #     return cubes

    # # Replace the client methods with mock versions
    # client.get_code_sets = mock_get_codesets
    # client.get_all_cubes_list_lite = mock_get_cubeslistlite
    
    return client

@pytest.fixture(scope="session")
def codesets_data(request: pytest.FixtureRequest) -> dict:
    return WDSDataPaths.CODESETS.load(request=request)


@pytest.fixture(scope="session")
def cubeslist_lite_data(request: pytest.FixtureRequest) -> list:
    return WDSDataPaths.CUBESLIST_LITE.load(request=request)


@pytest.fixture(scope="session")
def cubemeta_data(request: pytest.FixtureRequest) -> list:
    return WDSDataPaths.CUBEMETA.load(request=request)
