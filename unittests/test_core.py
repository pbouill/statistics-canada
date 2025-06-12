"""
Unit tests for the Census and DGUID functionality.
"""
import unittest
from statscan.enums.vintage import Vintage
try:
    from statscan.dguid import DGUID
    DGUID_AVAILABLE = True
except ImportError:
    DGUID_AVAILABLE = False


class TestCensusYear(unittest.TestCase):
    """Test cases for CensusYear enum."""
    
    def test_census_year_values(self):
        """Test that CensusYear enum has expected values."""
        self.assertEqual(Vintage.CENSUS_2021.value, 2021)
        # Note: Other vintage years are commented out in the actual implementation
    
    def test_census_year_membership(self):
        """Test that we can check membership in CensusYear."""
        self.assertIn(Vintage.CENSUS_2021, Vintage)
        
        # Test that we can access by value
        self.assertEqual(Vintage(2021), Vintage.CENSUS_2021)
        
        # Note: Other vintage years are commented out in the actual implementation
    
    def test_census_year_invalid(self):
        """Test handling of invalid census years."""
        with self.assertRaises(ValueError):
            Vintage(2022)  # Future year not in enum
        
        with self.assertRaises(ValueError):
            Vintage(1900)  # Too old


@unittest.skipUnless(DGUID_AVAILABLE, "DGUID module not available")
class TestDGUID(unittest.TestCase):
    """Test cases for DGUID functionality."""
    
    def test_dguid_creation(self):
        """Test DGUID creation and validation."""
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
        except ImportError:
            self.skipTest("ProvinceTerritory enum not available")
        
        # Test DGUID creation with required parameters
        dguid = DGUID(vintage=Vintage.CENSUS_2021, geocode=ProvinceTerritory.ONTARIO)
        
        self.assertEqual(dguid.vintage, Vintage.CENSUS_2021)
        self.assertEqual(dguid.geocode, ProvinceTerritory.ONTARIO)
    
    def test_dguid_comparison(self):
        """Test DGUID comparison operations."""
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
        except ImportError:
            self.skipTest("ProvinceTerritory enum not available")
        
        dguid1 = DGUID(vintage=Vintage.CENSUS_2021, geocode=ProvinceTerritory.ONTARIO)
        dguid2 = DGUID(vintage=Vintage.CENSUS_2021, geocode=ProvinceTerritory.ONTARIO)
        dguid3 = DGUID(vintage=Vintage.CENSUS_2021, geocode=ProvinceTerritory.QUEBEC)
        
        self.assertEqual(dguid1, dguid2)
        self.assertNotEqual(dguid1, dguid3)


class TestURLModule(unittest.TestCase):
    """Test cases for URL constants."""
    
    def test_url_constants_exist(self):
        """Test that URL constants are defined."""
        from statscan.url import GEO_ATTR_FILE_2021_URL
        
        self.assertIsInstance(GEO_ATTR_FILE_2021_URL, str)
        self.assertTrue(GEO_ATTR_FILE_2021_URL.startswith('https://'))
        self.assertIn('statcan.gc.ca', GEO_ATTR_FILE_2021_URL)
    
    def test_wds_base_url(self):
        """Test WDS base URL constant."""
        try:
            from statscan.url import WDS_BASE_URL
            self.assertIsInstance(WDS_BASE_URL, str)
            self.assertTrue(WDS_BASE_URL.startswith('https://'))
        except ImportError:
            self.skipTest("WDS_BASE_URL not available")


class TestPackageStructure(unittest.TestCase):
    """Test the overall package structure and imports."""
    
    def test_main_package_import(self):
        """Test that main package can be imported."""
        import statscan
        self.assertTrue(hasattr(statscan, '__version__'))
    
    def test_submodule_imports(self):
        """Test that submodules can be imported."""
        # Test util module
        from statscan.util import data
        self.assertTrue(hasattr(data, 'download_data'))
        self.assertTrue(hasattr(data, 'unpack_to_dataframe'))
        
        # Test enums module
        from statscan.enums import schema
        self.assertTrue(hasattr(schema, 'Schema'))
    
    def test_version_info_available(self):
        """Test that version information is available."""
        import statscan
        
        # Should have version info
        self.assertTrue(hasattr(statscan, '__version__'))
        self.assertIsInstance(statscan.__version__, str)
        
        # Version should be in expected format (YYYY.M.D.HHMMSS)
        version_parts = statscan.__version__.split('.')
        self.assertEqual(len(version_parts), 4)
        self.assertTrue(version_parts[0].isdigit())  # Year
        self.assertTrue(version_parts[1].isdigit())  # Month
        self.assertTrue(version_parts[2].isdigit())  # Day
        self.assertEqual(len(version_parts[3]), 6)   # HHMMSS


if __name__ == '__main__':
    unittest.main()
