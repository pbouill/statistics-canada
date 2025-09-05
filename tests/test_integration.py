"""
Integration tests for the statistics-canada package.
"""
import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, AsyncMock

from statscan.util.get_data import download_data, unpack_to_dataframe


class TestDataIntegration:
    """Integration tests for data downloading and processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('statscan.util.get_data.AsyncClient')
    def test_download_and_unpack_workflow(self, mock_client):
        """Test the complete workflow of downloading and unpacking data."""
        # Mock CSV data
        csv_content = b"Province,Code,Population\nOntario,35,14000000\nQuebec,24,8500000\n"
        
        # Mock HTTP response
        mock_response = mock_client.return_value.__aenter__.return_value.get.return_value
        mock_response.content = csv_content
        # Fix for coroutine warning: properly mock the synchronous method
        mock_response.raise_for_status = lambda: None
        
        async def run_integration_test():
            # Download the data
            file_path = await download_data(
                url="https://example.com/test.csv",
                data_dir=self.temp_dir,
                file_name="test_data.csv"
            )
            
            # Unpack to DataFrame
            df = unpack_to_dataframe(file_path)
            
            return df
        
        # Run the test
        df = asyncio.run(run_integration_test())
        
        # Verify the complete workflow
        assert len(df) == 2
        assert list(df.columns) == ['Province', 'Code', 'Population']
        assert df.iloc[0]['Province'] == 'Ontario'
        assert df.iloc[1]['Code'] == '24'


class TestEnumIntegration:
    """Integration tests for enum functionality."""
    
    def test_province_and_geolevel_integration(self):
        """Test integration between Province enum and GeoLevel."""
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
            from statscan.enums.schema import Schema
            
            # Test that province enum works with geo level
            ontario = ProvinceTerritory.ONTARIO
            
            # Test that we can get the schema (geo level)
            geo_level = ontario.get_schema()
            assert geo_level == Schema.PR
            
            # Test code generation
            code = ontario.code
            assert code.startswith('A0002')  # Province geo level code
            
            # Test UID
            uid = ontario.uid
            assert uid == '35'  # Ontario's province code
                
        except ImportError:
            pytest.skip("Province enum or GeoLevel not available")
    
    def test_census_division_integration(self):
        """Test census division enum integration."""
        try:
            from statscan.enums.auto.census_division import CensusDivision
            from statscan.enums.auto.province_territory import ProvinceTerritory
            
            # Get a census division
            divisions = list(CensusDivision)
            assert len(divisions) > 0
            
            # Test first division
            first_division = divisions[0]
            
            # Test that it has a province relationship if available
            if hasattr(first_division, 'province_territory'):
                province = first_division.province_territory
                assert isinstance(province, ProvinceTerritory)
                
        except ImportError:
            pytest.skip("Census division enum not available")


class TestBuildSystemIntegration:
    """Test build system and packaging integration."""
    
    def test_package_version_consistency(self):
        """Test that package version is consistent across modules."""
        import statscan
        from statscan._version import __version__
        
        # Version should be consistent
        assert statscan.__version__ == __version__
        
        # Version should be in expected format
        version_parts = __version__.split('.')
        assert len(version_parts) == 4
        
        # Should be able to parse as expected
        year, month, day, time_part = version_parts
        assert int(year) >= 2025
        assert int(month) >= 1
        assert int(month) <= 12
        assert int(day) >= 1
        assert int(day) <= 31
        assert len(time_part) == 6  # HHMMSS
    
    def test_imports_work_from_installed_package(self):
        """Test that all expected imports work."""
        # Main package
        import statscan
        assert hasattr(statscan, '__version__')
        
        # Core enums
        from statscan.enums.schema import Schema
        assert Schema is not None
        
        # Utility functions
        from statscan.util.get_data import download_data, unpack_to_dataframe
        assert callable(download_data)
        assert callable(unpack_to_dataframe)
        
        # Census functionality
        from statscan.enums.vintage import Vintage
        assert Vintage is not None


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_typical_user_workflow(self):
        """Test a typical user workflow."""
        # This would be what a real user might do:
        
        # 1. Import the package
        import statscan
        from statscan.enums.schema import Schema
        from statscan.enums.vintage import Vintage
        
        # 2. Check version
        version = statscan.__version__
        assert isinstance(version, str)
        
        # 3. Use enums
        canada_level = Schema.CAN
        assert canada_level == 'A0000'
        
        census_2021 = Vintage.CENSUS_2021
        assert census_2021.value == 2021
        
        # 4. Work with auto-generated enums (if available)
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
            ontario = ProvinceTerritory.ONTARIO
            assert ontario is not None
        except ImportError:
            # Acceptable if enums haven't been generated yet
            pass
    
    @patch('statscan.util.get_data.AsyncClient')
    def test_data_scientist_workflow(self, mock_client):
        """Test a workflow that a data scientist might use."""
        # Mock successful download
        csv_content = b"GeoLevel,Name,Value\nPR,Ontario,14000000\nPR,Quebec,8500000\n"
        mock_response = mock_client.return_value.__aenter__.return_value.get.return_value
        mock_response.content = csv_content
        mock_response.raise_for_status = lambda: None
        
        async def data_science_workflow():
            from statscan.util.get_data import download_data, unpack_to_dataframe
            
            # Download data
            file_path = await download_data(
                "https://example.com/census_data.csv",
                data_dir=self.temp_dir
            )
            
            # Load into DataFrame
            df = unpack_to_dataframe(file_path)
            
            # Basic data analysis
            province_data = df[df['GeoLevel'] == 'PR']
            total_population = province_data['Value'].astype(int).sum()
            
            return total_population, len(province_data)
        
        # Run the workflow
        total_pop, num_provinces = asyncio.run(data_science_workflow())
        
        # Verify results
        assert total_pop == 22500000  # Sum of Ontario + Quebec
        assert num_provinces == 2


if __name__ == '__main__':
    pytest.main([__file__])
