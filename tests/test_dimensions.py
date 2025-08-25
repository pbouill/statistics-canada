"""
Unit tests for SDMX dimension handling and data structure validation.
"""
import pytest
from statscan.sdmx.data.structure.dimensions import Dimensions
from statscan.sdmx.data.structure.dimension.series import Series as SeriesDimension  
from statscan.sdmx.data.structure.dimension.observation import Observation as ObservationDimension
from statscan.sdmx.data.structure.value import Value


class TestDimensions:
    """Test cases for SDMX dimension handling."""
    
    def test_dimensions_creation(self):
        """Test creating dimensions structure."""
        series_dims = [
            SeriesDimension(
                id="GENDER",
                name="Gender",
                names={"en": "Gender"},
                values=[
                    Value(id="T", name="Total", names={"en": "Total"}),
                    Value(id="M", name="Male", names={"en": "Male"}),
                    Value(id="F", name="Female", names={"en": "Female"})
                ]
            )
        ]
        
        obs_dims = [
            ObservationDimension(
                id="TIME_PERIOD",
                name="Time Period", 
                names={"en": "Time Period"},
                values=[
                    Value(id="2021", name="2021", names={"en": "2021"})
                ]
            )
        ]
        
        dimensions = Dimensions(series=series_dims, observation=obs_dims)
        
        assert len(dimensions.series) == 1
        assert len(dimensions.observation) == 1
        assert dimensions.series[0].id == "GENDER"
        assert dimensions.observation[0].id == "TIME_PERIOD"
    
    def test_dimension_value_access(self):
        """Test accessing dimension values."""
        values = [
            Value(id="T", name="Total", names={"en": "Total"}),
            Value(id="M", name="Male", names={"en": "Male"}),
            Value(id="F", name="Female", names={"en": "Female"})
        ]
        
        gender_dim = SeriesDimension(
            id="GENDER",
            name="Gender",
            names={"en": "Gender"},
            values=values
        )
        
        # Test direct access
        assert gender_dim.values[0].id == "T"
        assert gender_dim.values[1].name == "Male"
        
        # Test value lookup by ID
        male_value = next((v for v in gender_dim.values if v.id == "M"), None)
        assert male_value is not None
        assert male_value.name == "Male"
    
    def test_dimension_indexing(self):
        """Test dimension indexing capabilities."""
        values = [
            Value(id="0", name="Canada", names={"en": "Canada"}),
            Value(id="1", name="Ontario", names={"en": "Ontario"}),
            Value(id="2", name="Quebec", names={"en": "Quebec"})
        ]
        
        geo_dim = SeriesDimension(
            id="GEO",
            name="Geography",
            names={"en": "Geography"},
            values=values
        )
        
        # Test that we can iterate through values
        value_ids = [v.id for v in geo_dim.values]
        assert value_ids == ["0", "1", "2"]
        
        # Test that we can find values by properties
        canada_values = [v for v in geo_dim.values if "Canada" in v.name]
        assert len(canada_values) == 1
        assert canada_values[0].id == "0"


class TestDimensionValue:
    """Test cases for dimension value objects."""
    
    def test_value_creation(self):
        """Test creating dimension values."""
        value = Value(
            id="M",
            name="Male",
            names={"en": "Male", "fr": "Masculin"}
        )
        
        assert value.id == "M"
        assert value.name == "Male"
        assert value.names["en"] == "Male"
        assert value.names["fr"] == "Masculin"
    
    def test_value_display_name(self):
        """Test value display name functionality."""
        value = Value(
            id="M",
            name="Male",
            names={"en": "Male", "fr": "Masculin"}
        )
        
        # Test default (English) display name
        assert value.get_display_name() == "Male"
        
        # Test French display name
        assert value.get_display_name("fr") == "Masculin"
        
        # Test fallback to default name for unsupported language
        assert value.get_display_name("es") == "Male"
    
    def test_value_equality(self):
        """Test value equality comparison."""
        value1 = Value(id="M", name="Male", names={"en": "Male"})
        value2 = Value(id="M", name="Male", names={"en": "Male"})
        value3 = Value(id="F", name="Female", names={"en": "Female"})
        
        assert value1 == value2
        assert value1 != value3
        assert value2 != value3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
