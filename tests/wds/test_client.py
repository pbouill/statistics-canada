import json
from unittest.mock import AsyncMock

import pytest
from httpx import Response, Request

from statscan.wds.client import Client
from statscan.wds.requests import WDSRequests
from statscan.wds.models.code import CodeSets, CodeSet, Code
from statscan.wds.models.cube import Cube
from statscan.enums.auto.wds.scalar import Scalar

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
            content=json.dumps(json_data).encode('utf-8'),
            headers={"content-type": "application/json"},
            json=json_data,
        )


class TestWDSClient:
    """Test WDS Client functionality using mocked responses with local test data."""

    @mock_method(WDSRequests.get_code_sets)
    @pytest.mark.dependency(name='codesets')
    @pytest.mark.asyncio
    async def test_update_codesets_mocked(self, mock_method: AsyncMock, wds_client: Client, codesets_data: dict):
        """Test update_codesets using mocked responses."""
        # Set up the mock to use our mock method
        async def mock_side_effect(client: Client):
            return MockWDSResponse(codesets_data)
        mock_method.side_effect = mock_side_effect

        codeset_names = await wds_client.update_codesets()
        assert isinstance(codeset_names, set)
        mock_method.assert_called_once_with(client=wds_client)

    @pytest.mark.dependency(name='codesets')
    @pytest.mark.asyncio
    async def test_update_codesets_network(self, wds_client: Client):
        codeset_names = await wds_client.update_codesets()
        assert isinstance(codeset_names, set)

    @pytest.mark.dependency(depends=['codesets'])
    def test_codesets(self, wds_client: Client):
        """Test codesets property after updating codesets."""
        # codesets should be populated based on our dependencies
        assert isinstance(wds_client.codesets, CodeSets)

        # Now, codesets should be an instance of CodeSets
        assert isinstance(wds_client.codesets, CodeSets)
        assert "scalar" in wds_client.codesets.keys()
        scalar_codeset = wds_client.codesets[Scalar.__name__.lower()]
        assert isinstance(scalar_codeset, CodeSet)
        units_code = scalar_codeset[Scalar.UNITS.value]
        assert isinstance(units_code, Code)