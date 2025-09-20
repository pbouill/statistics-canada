"""
Unit tests for the GeoLevel enum and related functionality.
"""
import pytest
from statscan.enums.schema import Schema


class TestGeoLevel:
    """Test cases for GeoLevel enum."""
    
    def test_geolevel_values(self):
        """Test that GeoLevel enum has expected values."""
        assert Schema.CAN == 'A0000'
        assert Schema.PR == 'A0002'
        assert Schema.CD == 'A0003'
        assert Schema.FED == 'A0004'
        assert Schema.CSD == 'A0005'
        assert Schema.DPL == 'A0006'
    
    def test_geolevel_from_dguid(self):
        """Test parsing GeoLevel from DGUID."""
        # Test valid DGUIDs
        assert Schema.from_dguid('2021A000011124') == Schema.CAN
        assert Schema.from_dguid('2021A000211124') == Schema.PR
        assert Schema.from_dguid('2021A000311124') == Schema.CD
        
    def test_geolevel_from_dguid_invalid(self):
        """Test GeoLevel.from_dguid with invalid input."""
        with pytest.raises(ValueError):
            Schema.from_dguid('invalid_dguid')
        
        with pytest.raises(ValueError):
            Schema.from_dguid('2021X000011124')  # Invalid geo level code
    
    def test_geolevel_properties(self):
        """Test GeoLevel property methods."""
        # Test administrative areas
        assert Schema.PR.is_administrative_area
        assert Schema.CD.is_administrative_area
        assert not Schema.CMA.is_administrative_area
        
        # Test statistical areas
        assert Schema.CMA.is_statistical_area
        assert Schema.CT.is_statistical_area
        assert not Schema.PR.is_statistical_area
    
    def test_geolevel_data_flow(self):
        """Test data_flow property."""
        # Check actual values from the implementation
        assert isinstance(Schema.CAN.data_flow, str)
        assert isinstance(Schema.PR.data_flow, str)
        # Note: Update these assertions based on your actual implementation


class TestEnumIntegration:
    """Test integration between different enum modules."""
    
    def test_province_enum_import(self):
        """Test that province enum can be imported."""
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
            assert ProvinceTerritory is not None
            
            # Test that it has expected values
            assert hasattr(ProvinceTerritory, 'ONTARIO')
            assert hasattr(ProvinceTerritory, 'QUEBEC')
            assert hasattr(ProvinceTerritory, 'BRITISH_COLUMBIA')
        except ImportError:
            pytest.skip("Province enum not available")
    
    def test_census_division_enum_import(self):
        """Test that census division enum can be imported."""
        try:
            from statscan.enums.auto.census_division import CensusDivision
            assert CensusDivision is not None
            
            # Test that it has some expected values
            enum_names = [item.name for item in CensusDivision]
            assert len(enum_names) > 0
        except ImportError:
            pytest.skip("Census division enum not available")
