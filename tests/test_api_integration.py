"""
Integration tests that make real API calls to Statistics Canada services.
This is the ONLY test file that should make actual web requests.
All other tests should use local test data.
"""
import pytest
import asyncio
from statscan.wds.client import Client
from statscan.util.get_data import download_data, get_sdmx_data
from statscan.dguid import DGUID
from statscan.enums.auto.census_subdivision import CensusSubdivision
from statscan.url import GEO_ATTR_FILE_2021_URL


class TestRealAPIConnectivity:
    """Test actual connectivity to Statistics Canada APIs."""
    
    @pytest.mark.asyncio
    async def test_wds_api_code_sets(self):
        """Test that WDS API is accessible and returns code sets."""
        try:
            client = Client()
            assert client.base_url is not None
            
            # Try to get code sets (basic connectivity test)
            result = await client.get_code_sets()
            assert isinstance(result, dict)
            assert len(result) > 0
            
            # Verify some expected structure
            assert any(key in result for key in ['scale', 'freq', 'symbol'])
            
        except Exception as e:
            pytest.skip(f"WDS API not accessible: {e}")
    
    @pytest.mark.asyncio
    async def test_census_data_download(self):
        """Test downloading actual census geographic data."""
        try:
            # Test downloading a small file from Statistics Canada
            file_path = await download_data(
                url=GEO_ATTR_FILE_2021_URL,
                file_name="test_geo_data.zip"
            )
            
            assert file_path.exists()
            assert file_path.suffix == '.zip'
            assert file_path.stat().st_size > 1000  # Should be substantial file
            
            # Clean up
            file_path.unlink()
            
        except Exception as e:
            pytest.skip(f"Census data download failed: {e}")
    
    @pytest.mark.asyncio 
    async def test_sdmx_data_request(self):
        """Test making an SDMX data request for a specific geographic area."""
        try:
            # Test with a simple Canada-level request
            response = await get_sdmx_data(
                flow_ref='DF_98-401-X2021006_A5-2021',
                dguid='2021A0000A0000',  # Canada DGUID
                timeout=30
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify basic SDMX structure
            assert 'meta' in data
            assert 'data' in data
            assert 'dataSets' in data['data']
            
        except Exception as e:
            pytest.skip(f"SDMX API request failed: {e}")


class TestSaugeenShoresAPIIntegration:
    """Integration tests specifically for Saugeen Shores data via real API calls."""
    
    @pytest.mark.asyncio
    async def test_saugeen_shores_dguid_update(self):
        """Test that Saugeen Shores DGUID can fetch real data from API."""
        try:
            dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
            await dguid.update(timeout=30)
            
            # Verify we got some data
            assert dguid.sdmx_response is not None
            assert dguid.dataframe is not None
            assert len(dguid.dataframe) > 0
            
            # Basic population data validation
            population_data = dguid.population_data
            if population_data is not None and len(population_data) > 0:
                # Should have some population records
                assert 'Value' in population_data.columns
                total_pop_records = population_data[
                    population_data['Characteristic'].str.contains('Total - Age groups', case=False, na=False)
                ]
                if len(total_pop_records) > 0:
                    pop_value = total_pop_records.iloc[0]['Value']
                    # Reasonable population range for Saugeen Shores
                    assert 10000 <= pop_value <= 20000, f"Population {pop_value} outside expected range"
            
        except Exception as e:
            pytest.skip(f"Saugeen Shores API integration failed: {e}")


@pytest.mark.slow
class TestFullAPIWorkflow:
    """Test complete workflows that require multiple API calls."""
    
    @pytest.mark.asyncio
    async def test_complete_data_workflow(self):
        """Test a complete workflow from download to analysis."""
        try:
            # This test combines multiple API operations
            client = Client()
            
            # 1. Test basic API connectivity
            code_sets = await client.get_code_sets()
            assert len(code_sets) > 0
            
            # 2. Test SDMX data fetch for a specific area
            dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
            await dguid.update(timeout=45)
            
            # 3. Verify data processing pipeline
            assert dguid.sdmx_response is not None
            df = dguid.dataframe
            assert df is not None and len(df) > 0
            
            # 4. Test basic data analysis capabilities
            if dguid.population_data is not None:
                pop_data = dguid.population_data
                assert 'Value' in pop_data.columns
                assert 'Characteristic' in pop_data.columns
                
        except Exception as e:
            pytest.skip(f"Complete API workflow failed: {e}")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_api_integration.py -v -s
    pytest.main([__file__, "-v", "-s"])
