import json
import pytest
from pathlib import Path

from statscan.sdmx.data.dataset.series import Series
from statscan.sdmx.response import SDMXResponse
from statscan.sdmx.meta import Metadata
from statscan.sdmx.data.data import Data
from statscan.sdmx.data.dataset.dataset import Dataset

METADATA_ID = 'IREF420640'
METADATA_SENDER_ID = 'Stable_-_DotStat_v8'
DATASET_COUNT = 1
SERIES_COUNT = 1
TEST_SERIES_KEY = '0:0:0:0:0'

@pytest.fixture
def json_data() -> dict:
    """Load sample SDMX response data."""
    data_file = Path(__file__).parent / 'data' / 'sdmx' / 'sdmx_response.json'
    with data_file.open() as f:
        return json.load(f)

@pytest.fixture
def response(json_data: dict) -> SDMXResponse:
    """Test SDMXResponse model with sample data."""
    return SDMXResponse.model_validate(json_data)

@pytest.fixture
def metadata(response: SDMXResponse) -> Metadata:
    """Test Metadata model with sample data."""
    return response.meta

@pytest.fixture
def data(response: SDMXResponse) -> Data:
    """Test Data model with sample data."""
    return response.data

@pytest.fixture
def dataset(data: Data) -> Dataset:
    """Test Dataset model with sample data."""
    return data.dataSets[0]

@pytest.fixture
def series(dataset: Dataset) -> Series:
    """Test Series model with sample data."""
    return dataset.series[TEST_SERIES_KEY]



class TestSDMXModel:
    def test_metadata(self, metadata: Metadata):
        """Test metadata extraction."""
        assert isinstance(metadata, Metadata)
        assert metadata.id == METADATA_ID
        assert metadata.sender.id == METADATA_SENDER_ID

    def test_data(self, data: Data):
        """Test data extraction."""
        assert isinstance(data, Data)
        assert isinstance(data.dataSets, list)
        assert all(isinstance(ds, Dataset) for ds in data.dataSets)
        assert len(data.dataSets) == DATASET_COUNT

    
    def test_dataset(self, dataset: Dataset):
        """Test dataset properties."""
        assert isinstance(dataset, Dataset)
        assert TEST_SERIES_KEY in dataset.series

    # def test


