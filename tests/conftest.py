"""Pytest configuration and shared fixtures.

Provides fixtures for loading test data from tests/data/ directory.
Network tests are disabled by default and must be explicitly enabled with --network flag.
"""

import pytest

from statscan.wds.client import Client as WDSClient
from tests.data_store import SESSION_DATA_SAVED_ATTR, WDSDataPaths
from tests.wds.test_requests import (
    TestCodeSets,
    TestCubeMeta,
    TestCubesListLite,
)


def pytest_addoption(parser):
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--network",
        action="store_true",
        default=False,
        help="Enable network tests (disabled by default to avoid timeouts in CI/CD)",
    )


TRACKED_TESTS = {
    TestCodeSets.test_get_codesets.__name__: WDSDataPaths.CODESETS.name,
    TestCubesListLite.test_get_cubeslistlite.__name__: WDSDataPaths.CUBESLIST_LITE.name,
    TestCubeMeta.test_get_cubemetadata.__name__: WDSDataPaths.CUBEMETA.name,
}


def pytest_collection_modifyitems(config, items: list[pytest.Item]):
    """Modify test collection based on command-line flags.

    By default (without --network):
    - Network tests are automatically skipped
    - Tests use mocked data from tests/data/ directory

    With --network flag:
    - Network tests run first to generate/update fixture data
    - Then mocked tests run using the fresh data
    """
    network_enabled = config.getoption("--network")

    if not network_enabled:
        # Skip all network tests by default
        skip_network = pytest.mark.skip(reason="Network tests disabled (use --network to enable)")
        for item in items:
            if item.get_closest_marker("network"):
                item.add_marker(skip_network)
    else:
        # When network tests ARE enabled, prioritize them to generate fresh data first
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
    """Hook that runs after each test stage (setup, call, teardown).
    We use it to check if API requests tests have failed and track successful data saves.
    """
    if call.when == "call":
        if data_path_name := TRACKED_TESTS.get(item.name):
            if not isinstance(
                sd := getattr(item.session, SESSION_DATA_SAVED_ATTR, None), dict
            ):
                sd = {}
                setattr(item.session, SESSION_DATA_SAVED_ATTR, sd)
            sd[data_path_name] = (item.name, call.excinfo)


@pytest.fixture(scope="session")
def wds_client() -> WDSClient:
    """Provides a WDS client instance for test execution.

    Uses DEFAULT_WDS_TIMEOUT from client.py, which includes generous timeouts
    to handle intermittent TLS handshake delays observed with Statistics Canada
    servers, particularly affecting Python 3.13+.

    Note: http2=False is set in Client.__init__() defaults for reliability.
    """
    # Use default client configuration (includes 120s connect timeout and http2=False)
    return WDSClient()


@pytest.fixture(scope="session")
def codesets_data(request: pytest.FixtureRequest) -> dict:
    return WDSDataPaths.CODESETS.load(request=request)


@pytest.fixture(scope="session")
def cubeslist_lite_data(request: pytest.FixtureRequest) -> list:
    return WDSDataPaths.CUBESLIST_LITE.load(request=request)


@pytest.fixture(scope="session")
def cubemeta_data(request: pytest.FixtureRequest) -> list:
    return WDSDataPaths.CUBEMETA.load(request=request)
