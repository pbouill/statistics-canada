"""
Unit tests for the Census and DGUID functionality.
"""
import pytest
from statscan.enums.vintage import Vintage

try:
    from statscan.dguid import DGUID
    DGUID_AVAILABLE = True
except ImportError:
    DGUID_AVAILABLE = False


class TestCensusYear:
    """Test cases for CensusYear enum."""
    
    def test_census_year_values(self):
        """Test that CensusYear enum has expected values."""
        assert Vintage.CENSUS_2021.value == 2021
        # Note: Other vintage years are commented out in the actual implementation
    
    def test_census_year_membership(self):
        """Test that we can check membership in CensusYear."""
        assert Vintage.CENSUS_2021 in Vintage
        
        # Test that we can access by value
        assert Vintage(2021) == Vintage.CENSUS_2021
        
        # Note: Other vintage years are commented out in the actual implementation
    
    def test_census_year_invalid(self):
        """Test handling of invalid census years."""
        with pytest.raises(ValueError):
            Vintage(2022)  # Future year not in enum
        
        with pytest.raises(ValueError):
            Vintage(1900)  # Too old


@pytest.mark.skipif(not DGUID_AVAILABLE, reason="DGUID module not available")
class TestDGUID:
    """Test cases for DGUID functionality."""
    
    def test_dguid_creation(self):
        """Test DGUID creation and validation."""
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
        except ImportError:
            pytest.skip("ProvinceTerritory enum not available")
        
        # Test DGUID creation with required parameters
        dguid = DGUID(vintage=Vintage.CENSUS_2021, geocode=ProvinceTerritory.ONTARIO)
        
        assert dguid.vintage == Vintage.CENSUS_2021
        assert dguid.geocode == ProvinceTerritory.ONTARIO
    
    def test_dguid_comparison(self):
        """Test DGUID comparison operations."""
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
        except ImportError:
            pytest.skip("ProvinceTerritory enum not available")
        
        dguid1 = DGUID(vintage=Vintage.CENSUS_2021, geocode=ProvinceTerritory.ONTARIO)
        dguid2 = DGUID(vintage=Vintage.CENSUS_2021, geocode=ProvinceTerritory.ONTARIO)
        dguid3 = DGUID(vintage=Vintage.CENSUS_2021, geocode=ProvinceTerritory.QUEBEC)
        
        assert dguid1 == dguid2
        assert dguid1 != dguid3


class TestURLModule:
    """Test cases for URL constants."""
    
    def test_url_constants_exist(self):
        """Test that URL constants are defined."""
        from statscan.url import GEO_ATTR_FILE_2021_URL
        
        assert isinstance(GEO_ATTR_FILE_2021_URL, str)
        assert GEO_ATTR_FILE_2021_URL.startswith('https://')
        assert 'statcan.gc.ca' in GEO_ATTR_FILE_2021_URL
    
    def test_wds_base_url(self):
        """Test WDS base URL constant."""
        try:
            from statscan.url import CENSUS_SDMX_BASE_URL
            assert isinstance(CENSUS_SDMX_BASE_URL, str)
            assert CENSUS_SDMX_BASE_URL.startswith('https://')
        except ImportError:
            pytest.skip("WDS_BASE_URL not available")


class TestPackageStructure:
    """Test the overall package structure and imports."""
    
    def test_main_package_import(self):
        """Test that main package can be imported."""
        import statscan
        assert hasattr(statscan, '__version__')
    
    def test_submodule_imports(self):
        """Test that submodules can be imported."""
        # Test util module
        from statscan.util import get_data
        assert hasattr(get_data, 'download_data')
        assert hasattr(get_data, 'unpack_to_dataframe')
        
        # Test enums module
        from statscan.enums import schema
        assert hasattr(schema, 'Schema')
    
    def test_version_info_available(self):
        """Test that version information is available."""
        import statscan
        
        # Should have version info
        assert hasattr(statscan, '__version__')
        assert isinstance(statscan.__version__, str)
        
        # Version should be in expected format (YYYY.M.D.HHMMSS)
        version_parts = statscan.__version__.split('.')
        assert len(version_parts) == 4
        assert version_parts[0].isdigit()  # Year
        assert version_parts[1].isdigit()  # Month
        assert version_parts[2].isdigit()  # Day
        assert len(version_parts[3]) == 6   # HHMMSS
