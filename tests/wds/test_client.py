import json

import pytest
from httpx import Request, Response

from statscan.enums.auto.wds.scalar import Scalar
from statscan.wds.client import Client
from statscan.wds.models.code import Code, CodeSet, CodeSets
from statscan.wds.requests import WDSRequests
from tests.mock_method import mock_method


class MockWDSResponse(Response):
    """Mock response class that inherits from httpx Response for WDS API responses."""

    def __init__(self, json_data: dict | list, status_code: int = 200):
        # Create a minimal request object for the parent constructor
        request = Request("GET", "https://www.statcan.gc.ca/api/wds/v1/mock")

        # Call parent constructor with minimal required parameters
        super().__init__(
            status_code=status_code,
            request=request,
            content=json.dumps(json_data).encode("utf-8"),
            headers={"content-type": "application/json"},
            json=json_data,
        )


class TestWDSClient:
    """Test WDS Client functionality using mocked responses with local test data."""

    @mock_method(WDSRequests.get_code_sets)
    @pytest.mark.asyncio
    async def test_update_codesets_mocked(
        self,
        mock_get_code_sets,
        wds_client: Client,
        codesets_data: dict,
    ):
        """Test update_codesets using mocked responses from tests/data."""
        # Set up the mock to return our test data
        async def mock_side_effect(client: Client):
            return MockWDSResponse(codesets_data)

        mock_get_code_sets.side_effect = mock_side_effect

        codeset_names = await wds_client.update_codesets()
        assert isinstance(codeset_names, set)
        mock_get_code_sets.assert_called_once_with(client=wds_client)

    @pytest.mark.asyncio
    @pytest.mark.network
    async def test_update_codesets_network(self, wds_client: Client):
        """Test update_codesets with real network calls.

        Only runs when --network flag is provided.
        Generates/updates test fixture data in tests/data/ directory.
        """
        codeset_names = await wds_client.update_codesets()
        assert isinstance(codeset_names, set)

    def test_codesets(self, wds_client: Client):
        """Test codesets property using mocked data.

        This test runs after update_codesets_mocked populates the client.
        """
        # codesets should be populated from the mocked update
        assert isinstance(wds_client.codesets, CodeSets)
        assert "scalar" in wds_client.codesets.keys()

        scalar_codeset = wds_client.codesets[Scalar.__name__.lower()]
        assert isinstance(scalar_codeset, CodeSet)

        units_code = scalar_codeset[Scalar.UNITS.value]
        assert isinstance(units_code, Code)
