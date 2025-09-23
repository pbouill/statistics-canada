import pytest

from statscan.wds.requests import WDSRequests, ResponseKeys, RESPONSE_SUCCESS_STR
from statscan.wds.client import Client

from tests.data_store import WDSDataPaths


class TestCodeSets:
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_get_codesets(self, wds_client: Client) -> None:
        response = await WDSRequests.get_code_sets(client=wds_client)
        response.raise_for_status()
        data = response.json()
        WDSDataPaths.CODESETS.save(data=data)

    def test_codesets_data(self, codesets_data: dict):
        assert isinstance(codesets_data, dict)
        assert ResponseKeys.STATUS in codesets_data
        assert codesets_data[ResponseKeys.STATUS] == RESPONSE_SUCCESS_STR

class TestCubesListLite:
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_get_cubeslistlite(self, wds_client: Client) -> None:
        response = await WDSRequests.get_all_cubes_list_lite(client=wds_client)
        response.raise_for_status()
        data = response.json()
        WDSDataPaths.CUBESLIST_LITE.save(data=data)

    def test_cubeslist_lite_data(self, cubeslist_lite_data: list[dict]):
        assert isinstance(cubeslist_lite_data, list)
        assert len(cubeslist_lite_data) > 0
        assert isinstance(cubeslist_lite_data[0], dict)


@pytest.fixture
def first_cube_product_id(cubeslist_lite_data: list[dict]) -> int:
    """Get the first cube product ID from stored cubes list data."""
    return cubeslist_lite_data[0]["productId"]


class TestCubeMeta:
    @pytest.mark.network
    @pytest.mark.asyncio
    async def test_get_cubemetadata(
        self, 
        wds_client: Client, 
        first_cube_product_id: int
    ) -> None:
        response = await WDSRequests.get_cube_metadata(
            client=wds_client, 
            product_id=first_cube_product_id
        )
        response.raise_for_status()
        data = response.json()
        WDSDataPaths.CUBEMETA.save(data=data)

    def test_cubemeta_data(self, cubemeta_data: list, first_cube_product_id: int):
        assert isinstance(cubemeta_data, list)
        assert len(cubemeta_data) > 0
        first_cubemeta = cubemeta_data[0]
        assert isinstance(first_cubemeta, dict)
        assert ResponseKeys.STATUS in first_cubemeta
        assert first_cubemeta[ResponseKeys.STATUS] == RESPONSE_SUCCESS_STR
        assert ResponseKeys.OBJECT in first_cubemeta
        first_cubemeta_object = first_cubemeta[ResponseKeys.OBJECT]
        assert isinstance(first_cubemeta_object, dict)
        assert 'productId' in first_cubemeta_object
        assert int(first_cubemeta_object['productId']) == first_cube_product_id
