"""
Integration tests for the statistics-canada package.
"""
import unittest
import asyncio
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch

from statscan.util.get_data import download_data, unpack_to_dataframe


class TestDataIntegration(unittest.TestCase):
    """Integration tests for data downloading and processing."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    @patch('statscan.util.data.AsyncClient')
    def test_download_and_unpack_workflow(self, mock_client):
        """Test the complete workflow of downloading and unpacking data."""
        # Mock CSV data
        csv_content = b"Province,Code,Population\nOntario,35,14000000\nQuebec,24,8500000\n"
        
        # Mock HTTP response
        mock_response = mock_client.return_value.__aenter__.return_value.get.return_value
        mock_response.content = csv_content
        # Fix for coroutine warning: properly mock the awaitable
        mock_response.raise_for_status = unittest.mock.AsyncMock(return_value=None)
        
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
        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['Province', 'Code', 'Population'])
        self.assertEqual(df.iloc[0]['Province'], 'Ontario')
        self.assertEqual(df.iloc[1]['Code'], '24')


class TestEnumIntegration(unittest.TestCase):
    """Integration tests for enum functionality."""
    
    def test_province_and_geolevel_integration(self):
        """Test integration between Province enum and GeoLevel."""
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
            from statscan.enums.schema import Schema
            
            # Test that province enum works with geo level
            ontario = ProvinceTerritory.ONTARIO
            
            # Test that we can get the geo level
            geo_level = ontario.get_geo_level()
            self.assertEqual(geo_level, Schema.PR)
            
            # Test DGUID generation if available
            if hasattr(ontario, 'dguid'):
                dguid = ontario.dguid
                self.assertTrue(dguid.startswith('2021'))
                self.assertIn('A0002', dguid)  # Province geo level code
                
        except ImportError:
            self.skipTest("Province enum or GeoLevel not available")
    
    def test_census_division_integration(self):
        """Test census division enum integration."""
        try:
            from statscan.enums.auto.census_division import CensusDivision
            from statscan.enums.auto.province_territory import ProvinceTerritory
            
            # Get a census division
            divisions = list(CensusDivision)
            self.assertGreater(len(divisions), 0)
            
            # Test first division
            first_division = divisions[0]
            
            # Test that it has a province relationship if available
            if hasattr(first_division, 'province_territory'):
                province = first_division.province_territory
                self.assertIsInstance(province, ProvinceTerritory)
                
        except ImportError:
            self.skipTest("Census division enum not available")


class TestBuildSystemIntegration(unittest.TestCase):
    """Test build system and packaging integration."""
    
    def test_package_version_consistency(self):
        """Test that package version is consistent across modules."""
        import statscan
        from statscan._version import __version__
        
        # Version should be consistent
        self.assertEqual(statscan.__version__, __version__)
        
        # Version should be in expected format
        version_parts = __version__.split('.')
        self.assertEqual(len(version_parts), 4)
        
        # Should be able to parse as expected
        year, month, day, time_part = version_parts
        self.assertGreaterEqual(int(year), 2025)
        self.assertGreaterEqual(int(month), 1)
        self.assertLessEqual(int(month), 12)
        self.assertGreaterEqual(int(day), 1)
        self.assertLessEqual(int(day), 31)
        self.assertEqual(len(time_part), 6)  # HHMMSS
    
    def test_imports_work_from_installed_package(self):
        """Test that all expected imports work."""
        # Main package
        import statscan
        self.assertTrue(hasattr(statscan, '__version__'))
        
        # Core enums
        from statscan.enums.schema import Schema
        self.assertIsNotNone(Schema)
        
        # Utility functions
        from statscan.util.get_data import download_data, unpack_to_dataframe
        self.assertTrue(callable(download_data))
        self.assertTrue(callable(unpack_to_dataframe))
        
        # Census functionality
        from statscan.enums.vintage import Vintage
        self.assertIsNotNone(Vintage)


class TestRealWorldScenarios(unittest.TestCase):
    """Test realistic usage scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
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
        self.assertIsInstance(version, str)
        
        # 3. Use enums
        canada_level = Schema.CAN
        self.assertEqual(canada_level, 'A0000')
        
        census_2021 = Vintage.CENSUS_2021
        self.assertEqual(census_2021.value, 2021)
        
        # 4. Work with auto-generated enums (if available)
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
            ontario = ProvinceTerritory.ONTARIO
            self.assertIsNotNone(ontario)
        except ImportError:
            # Acceptable if enums haven't been generated yet
            pass
    
    @patch('statscan.util.data.AsyncClient')
    def test_data_scientist_workflow(self, mock_client):
        """Test a workflow that a data scientist might use."""
        # Mock successful download
        csv_content = b"GeoLevel,Name,Value\nPR,Ontario,14000000\nPR,Quebec,8500000\n"
        mock_response = mock_client.return_value.__aenter__.return_value.get.return_value
        mock_response.content = csv_content
        mock_response.raise_for_status.return_value = None
        
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
        self.assertEqual(total_pop, 22500000)  # Sum of Ontario + Quebec
        self.assertEqual(num_provinces, 2)


if __name__ == '__main__':
    unittest.main()
