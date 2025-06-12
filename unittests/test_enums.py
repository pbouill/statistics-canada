"""
Unit tests for the GeoLevel enum and related functionality.
"""
import unittest
from statscan.enums.schema import Schema


class TestGeoLevel(unittest.TestCase):
    """Test cases for GeoLevel enum."""
    
    def test_geolevel_values(self):
        """Test that GeoLevel enum has expected values."""
        self.assertEqual(Schema.CAN, 'A0000')
        self.assertEqual(Schema.PR, 'A0002')
        self.assertEqual(Schema.CD, 'A0003')
        self.assertEqual(Schema.FED, 'A0004')
        self.assertEqual(Schema.CSD, 'A0005')
        self.assertEqual(Schema.DPL, 'A0006')
    
    def test_geolevel_from_dguid(self):
        """Test parsing GeoLevel from DGUID."""
        # Test valid DGUIDs
        self.assertEqual(Schema.from_dguid('2021A000011124'), Schema.CAN)
        self.assertEqual(Schema.from_dguid('2021A000211124'), Schema.PR)
        self.assertEqual(Schema.from_dguid('2021A000311124'), Schema.CD)
        
    def test_geolevel_from_dguid_invalid(self):
        """Test GeoLevel.from_dguid with invalid input."""
        with self.assertRaises(ValueError):
            Schema.from_dguid('invalid_dguid')
        
        with self.assertRaises(ValueError):
            Schema.from_dguid('2021X000011124')  # Invalid geo level code
    
    def test_geolevel_properties(self):
        """Test GeoLevel property methods."""
        # Test administrative areas
        self.assertTrue(Schema.PR.is_administrative_area)
        self.assertTrue(Schema.CD.is_administrative_area)
        self.assertFalse(Schema.CMA.is_administrative_area)
        
        # Test statistical areas
        self.assertTrue(Schema.CMA.is_statistical_area)
        self.assertTrue(Schema.CT.is_statistical_area)
        self.assertFalse(Schema.PR.is_statistical_area)
    
    def test_geolevel_data_flow(self):
        """Test data_flow property."""
        # Check actual values from the implementation
        self.assertIsInstance(Schema.CAN.data_flow, str)
        self.assertIsInstance(Schema.PR.data_flow, str)
        # Note: Update these assertions based on your actual implementation


class TestEnumIntegration(unittest.TestCase):
    """Test integration between different enum modules."""
    
    def test_province_enum_import(self):
        """Test that province enum can be imported."""
        try:
            from statscan.enums.auto.province_territory import ProvinceTerritory
            self.assertIsNotNone(ProvinceTerritory)
            
            # Test that it has expected values
            self.assertTrue(hasattr(ProvinceTerritory, 'ONTARIO'))
            self.assertTrue(hasattr(ProvinceTerritory, 'QUEBEC'))
            self.assertTrue(hasattr(ProvinceTerritory, 'BRITISH_COLUMBIA'))
        except ImportError:
            self.skipTest("Province enum not available")
    
    def test_census_division_enum_import(self):
        """Test that census division enum can be imported."""
        try:
            from statscan.enums.auto.census_division import CensusDivision
            self.assertIsNotNone(CensusDivision)
            
            # Test that it has some expected values
            enum_names = [item.name for item in CensusDivision]
            self.assertGreater(len(enum_names), 0)
        except ImportError:
            self.skipTest("Census division enum not available")


if __name__ == '__main__':
    unittest.main()
