"""
Unit tests for the Census and DGUID functionality.
"""
import unittest
from statscan.census import CensusYear
try:
    from statscan.dguid import DGUID
    DGUID_AVAILABLE = True
except ImportError:
    DGUID_AVAILABLE = False


class TestCensusYear(unittest.TestCase):
    """Test cases for CensusYear enum."""
    
    def test_census_year_values(self):
        """Test that CensusYear enum has expected values."""
        self.assertEqual(CensusYear.CENSUS_2021.value, 2021)
        self.assertEqual(CensusYear.CENSUS_2016.value, 2016)
        self.assertEqual(CensusYear.CENSUS_2011.value, 2011)
        self.assertEqual(CensusYear.CENSUS_2006.value, 2006)
    
    def test_census_year_membership(self):
        """Test that we can check membership in CensusYear."""
        self.assertIn(CensusYear.CENSUS_2021, CensusYear)
        self.assertIn(CensusYear.CENSUS_2016, CensusYear)
        
        # Test that we can access by value
        self.assertEqual(CensusYear(2021), CensusYear.CENSUS_2021)
        self.assertEqual(CensusYear(2016), CensusYear.CENSUS_2016)
    
    def test_census_year_invalid(self):
        """Test handling of invalid census years."""
        with self.assertRaises(ValueError):
            CensusYear(2022)  # Future year not in enum
        
        with self.assertRaises(ValueError):
            CensusYear(1900)  # Too old


@unittest.skipUnless(DGUID_AVAILABLE, "DGUID module not available")
class TestDGUID(unittest.TestCase):
    """Test cases for DGUID functionality."""
    
    def test_dguid_creation(self):
        """Test DGUID creation and validation."""
        from statscan.enums.auto.province import ProvinceTerritory
        
        # Test DGUID creation with required parameters
        dguid = DGUID(vintage=2021, province_territory=ProvinceTerritory.ONTARIO)
        
        self.assertEqual(dguid.vintage, 2021)
        self.assertEqual(dguid.province_territory, ProvinceTerritory.ONTARIO)
    
    def test_dguid_comparison(self):
        """Test DGUID comparison operations."""
        from statscan.enums.auto.province import ProvinceTerritory
        
        dguid1 = DGUID(vintage=2021, province_territory=ProvinceTerritory.ONTARIO)
        dguid2 = DGUID(vintage=2021, province_territory=ProvinceTerritory.ONTARIO)
        dguid3 = DGUID(vintage=2021, province_territory=ProvinceTerritory.QUEBEC)
        
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
        from statscan.enums import geolevel
        self.assertTrue(hasattr(geolevel, 'GeoLevel'))
    
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
