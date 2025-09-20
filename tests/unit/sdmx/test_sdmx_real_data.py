"""
Test SDMX models against actual Statistics Canada response data.
"""
import json
import pytest
from pathlib import Path
from statscan.sdmx.response import SDMXResponse


class TestSDMXRealData:
    """Test SDMX models with real Statistics Canada data."""
    
    @pytest.fixture
    def sample_response_data(self):
        """Load sample SDMX response data."""
        data_file = Path(__file__).parent.parent / "data" / "A5.2021A000235.1..1.json"
        if not data_file.exists():
            pytest.skip(f"Sample data file not found: {data_file}")
        
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def test_parse_real_sdmx_response(self, sample_response_data):
        """Test parsing a real SDMX response from Statistics Canada."""
        try:
            # Try to create an SDMXResponse from the real data
            response = SDMXResponse(**sample_response_data)
            
            # Basic validation
            assert response.meta is not None
            assert response.data is not None
            assert response.meta.id is not None
            assert response.meta.sender is not None
            
            print(f"Response ID: {response.meta.id}")
            print(f"Sender: {response.meta.sender.name}")
            print(f"Structures count: {len(response.data.structures) if response.data.structures else 0}")
            print(f"Datasets count: {len(response.data.dataSets) if response.data.dataSets else 0}")
            
        except Exception as e:
            # Print the structure to understand what we're working with
            print("=== ACTUAL RESPONSE STRUCTURE ===")
            print("Meta keys:", list(sample_response_data.get('meta', {}).keys()))
            print("Data keys:", list(sample_response_data.get('data', {}).keys()))
            
            meta_sample = sample_response_data.get('meta', {})
            if 'sender' in meta_sample:
                print("Sender keys:", list(meta_sample['sender'].keys()))
            
            data_sample = sample_response_data.get('data', {})
            if 'structures' in data_sample and data_sample['structures']:
                structure_sample = data_sample['structures'][0]
                print("Structure keys:", list(structure_sample.keys()))
                if 'dimensions' in structure_sample:
                    print("Dimensions keys:", list(structure_sample['dimensions'].keys()))
            
            raise e
    
    def test_dataframe_conversion(self, sample_response_data):
        """Test converting SDMX response to DataFrame."""
        try:
            # Create response and test DataFrame conversion
            response = SDMXResponse(**sample_response_data)
            response._raw_data = sample_response_data  # Store raw data for DataFrame conversion
            
            df = response.to_dataframe()
            
            assert not df.empty, "DataFrame should not be empty"
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {list(df.columns)}")
            
            # Validate expected columns
            expected_columns = ['series_key', 'time_period', 'value']
            for col in expected_columns:
                assert col in df.columns, f"Expected column '{col}' not found"
                
        except Exception as e:
            print(f"DataFrame conversion failed: {e}")
            # Still create the response object to test model validation
            response = SDMXResponse(**sample_response_data)
            response._raw_data = sample_response_data
            raise e


if __name__ == "__main__":
    # Allow running this test directly to see the structure
    test_instance = TestSDMXRealData()
    
    # Load the data manually for inspection
    data_file = Path(__file__).parent.parent / "data" / "A5.2021A000235.1..1.json"
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        test_instance.test_parse_real_sdmx_response(data)
    else:
        print(f"Data file not found: {data_file}")
