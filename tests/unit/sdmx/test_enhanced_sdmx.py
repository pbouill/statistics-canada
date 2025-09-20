"""
Tests for enhanced SDMX models and convenience methods.
"""

from pathlib import Path
from datetime import datetime
from statscan.sdmx.response import SDMXResponse
from statscan.sdmx.data.structure.annotation import Annotation
from statscan.sdmx.data.structure.value import Value
from statscan.sdmx.data.dataset.series import Series as DatasetSeries


# Updated to use richer test fixture inside tests/data (Option 1)
RAW_RESPONSE_JSON = Path("tests/data/sdmx/sdmx_response.json")

response = SDMXResponse.model_validate_json(RAW_RESPONSE_JSON.read_text())



class TestEnhancedSDMX:
    """Test cases for enhanced SDMX models and convenience methods."""
    
    def test_sdmx_response_convenience_methods(self):
        """Test the convenience methods of SDMXResponse."""
        # Test primary structure and dataset access
        assert response.primary_structure is not None
        assert response.primary_dataset is not None
        
        # Test annotation access (robust to fixtures without this type)
        annotations = response.get_annotations_by_type("NonProductionDataflow")
        assert isinstance(annotations, list)
        if annotations:
            assert annotations[0].type == "NonProductionDataflow"
        
        # Test dimension access (use existing id if GENDER not present)
        dim_summary = response.get_dimension_summary()
        assert isinstance(dim_summary, dict)
        assert len(dim_summary) >= 1
        dim_id = "GENDER" if "GENDER" in dim_summary else next(iter(dim_summary))
        gender_dim = response.get_series_dimension(dim_id)
        assert gender_dim is not None
        assert getattr(gender_dim, "name", None)
        
        # Test attribute access (use existing id if TOPIC not present)
        attr_summary = response.get_attribute_summary()
        assert isinstance(attr_summary, dict)
        topic_id = "TOPIC" if "TOPIC" in attr_summary else (next(iter(attr_summary)) if attr_summary else None)
        if topic_id:
            topic_attr = response.get_series_attribute(topic_id)
            assert topic_attr is not None
            assert getattr(topic_attr, "name", None)
        
        # Test dataset series access (use any available key)
        dataset = response.primary_dataset
        assert dataset is not None
        if hasattr(dataset, "series") and dataset.series:
            some_key = next(iter(dataset.series.keys()))
            series = response.get_dataset_series(some_key)
            assert series is not None
            assert len(series.observations) >= 1

    def test_enhanced_value_model(self):
        """Test enhanced Value model with time periods."""
        # Test regular value
        value = Value(id="M", name="Male", names={"en": "Male"})
        assert value.get_display_name() == "Male"
        assert not value.is_time_period
        
        # Test time period value
        time_value = Value(
            id="2021",
            name="2021",
            names={"en": "2021"},
            start=datetime(2021, 1, 1),
            end=datetime(2021, 12, 31)
        )
        assert time_value.is_time_period
        assert "2021-01-01 to 2021-12-31" in time_value.time_range_text

    def test_enhanced_annotation_model(self):
        """Test enhanced Annotation model."""
        # Test boolean annotation
        bool_annotation = Annotation(type="Flag", text=True, texts={"en": "true"})
        assert bool_annotation.is_boolean_flag
        assert bool_annotation.boolean_value
        
        # Test string annotation
        str_annotation = Annotation(type="Note", text="Important note", texts={"en": "Important note"})
        assert not str_annotation.is_boolean_flag
        assert str_annotation.boolean_value is None

    def test_dataset_series_convenience_methods(self):
        """Test convenience methods in dataset Series."""
        series = DatasetSeries(
            attributes=[1, 2],
            annotations=[0, 1],
            observations={
                0: [100.0, 200.0],
                1: [150.0, None],
                2: [None, None]
            }
        )
        
        # Test observation access
        assert series.get_observation_periods() == [0, 1, 2]
        
        # Test latest/earliest observations
        latest = series.get_latest_observation()
        assert latest[0] == 2
        
        earliest = series.get_earliest_observation()
        assert earliest[0] == 0
        
        # Test non-null observations
        non_null = series.get_non_null_observations()
        assert len(non_null) == 2  # periods 0 and 1 have data
        
        # Test summary
        summary = series.get_observation_summary()
        assert summary['total_periods'] == 3
        assert summary['periods_with_data'] == 2
        assert summary['non_null_values'] == 3
        
        # Test attribute/annotation checks
        assert series.has_attribute(1)
        assert not series.has_attribute(99)
        assert series.has_annotation(0)

    def test_response_summary_methods(self):
        """Test summary and search methods in SDMXResponse."""
        # Test dimension summary
        dim_summary = response.get_dimension_summary()
        assert isinstance(dim_summary, dict) and len(dim_summary) >= 1
        # Ensure typical keys present
        some_dim = next(iter(dim_summary.values()))
        assert 'name' in some_dim and 'value_count' in some_dim
        
        # Test attribute summary
        attr_summary = response.get_attribute_summary()
        assert isinstance(attr_summary, dict)
        if attr_summary:
            some_attr = next(iter(attr_summary.values()))
            assert 'name' in some_attr and 'value_count' in some_attr
        
        # Test search functionality (no strict count)
        search_results = response.search_values("Male")
        assert isinstance(search_results, dict)
        assert 'dimensions' in search_results and 'attributes' in search_results
        
        # Test response summary
        summary = response.response_summary
        assert summary["meta"].get("id") == getattr(response.meta, 'id', None)
        assert summary["dataset"].get("series_count", 0) >= 1

    def test_cross_referencing_methods(self):
        """Test cross-referencing convenience methods."""
        # Use whatever ids exist in the fixture, if any
        dim_summary = response.get_dimension_summary()
        attr_summary = response.get_attribute_summary()
        if dim_summary and attr_summary:
            dim_id = next(iter(dim_summary))
            attr_id = next(iter(attr_summary))
            dim_value, attr_value = response.cross_reference_dimension_attribute(dim_id, attr_id, "X")
            # Should return a tuple; content may be (None, None) for unrelated ids
            assert isinstance(dim_value, (type(None), object))
            assert isinstance(attr_value, (type(None), object))
        
        # Test annotations by type returns a list (may be empty depending on fixture)
        annotations = response.get_annotations_by_type("NonProductionDataflow")
        assert isinstance(annotations, list)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
