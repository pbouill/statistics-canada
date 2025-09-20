"""
Unit tests for SDMX data models and structures.
"""
import pytest
from datetime import datetime
from statscan.sdmx.base import Base
from statscan.sdmx.meta import Metadata, Sender
from statscan.sdmx.data.data import Data
from statscan.sdmx.data.structure.structure import Structure
from statscan.sdmx.data.structure.annotation import Annotation
from statscan.sdmx.response import SDMXResponse


class TestSDMXBase:
    """Test cases for the base SDMX model."""
    
    def test_base_model_creation(self):
        """Test creating base SDMX model."""
        # Base is abstract, but we can test its functionality through subclasses
        sender = Sender(
            id="STC",
            name="Statistics Canada",
            names={"en": "Statistics Canada", "fr": "Statistique Canada"}
        )
        
        assert sender.id == "STC"
        assert sender.name == "Statistics Canada"
        assert sender.get_display_name() == "Statistics Canada"
        assert sender.get_display_name("fr") == "Statistique Canada"


class TestSDMXMetadata:
    """Test cases for SDMX metadata structures."""
    
    def test_sender_creation(self):
        """Test creating sender metadata."""
        sender = Sender(
            id="STC",
            name="Statistics Canada",
            names={"en": "Statistics Canada", "fr": "Statistique Canada"},
            contacts=["contact@statcan.gc.ca"]
        )
        
        assert sender.id == "STC"
        assert sender.name == "Statistics Canada"
        assert len(sender.contacts) == 1
        assert sender.contacts[0] == "contact@statcan.gc.ca"
    
    def test_metadata_creation(self):
        """Test creating metadata structure."""
        sender = Sender(
            id="STC",
            name="Statistics Canada",
            names={"en": "Statistics Canada"}
        )
        
        metadata = Metadata(
            response_schema="2.1.0",
            id="test-response",
            test=True,
            prepared=datetime(2021, 1, 1, 12, 0, 0),
            sender=sender
        )
        
        assert metadata.response_schema == "2.1.0"
        assert metadata.id == "test-response"
        assert metadata.test is True
        assert metadata.prepared.year == 2021
        assert metadata.sender.id == "STC"


class TestSDMXAnnotation:
    """Test cases for SDMX annotations."""
    
    def test_annotation_creation(self):
        """Test creating annotations."""
        annotation = Annotation(
            type="NonProductionDataflow",
            text="Test data",
            texts={"en": "Test data", "fr": "Données de test"}
        )
        
        assert annotation.type == "NonProductionDataflow"
        assert annotation.text == "Test data"
        assert annotation.get_display_text() == "Test data"
        assert annotation.get_display_text("fr") == "Données de test"
    
    def test_boolean_annotation(self):
        """Test boolean annotation handling."""
        bool_annotation = Annotation(
            type="Flag",
            text=True,
            texts={"en": "true"}
        )
        
        assert bool_annotation.is_boolean_flag
        assert bool_annotation.boolean_value is True
        
        # Test with string boolean
        str_bool_annotation = Annotation(
            type="Flag", 
            text="true",
            texts={"en": "true"}
        )
        
        assert str_bool_annotation.is_boolean_flag
        assert str_bool_annotation.boolean_value is True


class TestSDMXStructure:
    """Test cases for SDMX data structures."""
    
    def test_structure_creation(self):
        """Test creating data structure."""
        structure = Structure(
            name="TestStructure",
            names={"en": "Test Structure", "fr": "Structure de test"},
            dimensions=None,  # Would be populated with actual dimensions
            attributes=None,  # Would be populated with actual attributes
            annotations=[],
            dataSets=[]
        )
        
        assert structure.name == "TestStructure"
        assert structure.get_display_name() == "Test Structure"
        assert structure.get_display_name("fr") == "Structure de test"
    
    def test_structure_summary(self):
        """Test structure summary functionality."""
        structure = Structure(
            name="TestStructure",
            names={"en": "Test Structure"},
            dimensions=None,
            attributes=None,
            annotations=[
                Annotation(type="Note", text="Test note", texts={"en": "Test note"})
            ],
            dataSets=[]
        )
        
        summary = structure.summary
        assert summary['name'] == "TestStructure"
        assert summary['annotations'] == 1
        assert summary['datasets'] == 0


class TestSDMXResponse:
    """Test cases for complete SDMX response handling."""
    
    def test_response_creation(self):
        """Test creating SDMX response."""
        sender = Sender(id="STC", name="Statistics Canada", names={"en": "Statistics Canada"})
        metadata = Metadata(
            response_schema="2.1.0",
            id="test-response",
            sender=sender,
            prepared=datetime.now()
        )
        
        data = Data(structures=[], dataSets=[])
        
        response = SDMXResponse(
            meta=metadata,
            data=data,
            errors=[]
        )
        
        assert response.meta.id == "test-response"
        assert response.meta.sender.id == "STC"
        assert len(response.errors) == 0
        assert response.data is not None
    
    def test_response_convenience_methods(self):
        """Test response convenience methods."""
        # Create minimal response for testing
        sender = Sender(id="STC", name="Statistics Canada", names={"en": "Statistics Canada"})
        metadata = Metadata(
            response_schema="2.1.0",
            id="test-response", 
            sender=sender,
            prepared=datetime.now()
        )
        
        data = Data(structures=[], dataSets=[])
        
        response = SDMXResponse(
            meta=metadata,
            data=data,
            errors=[]
        )
        
        # Test primary structure/dataset access (should be None for empty data)
        assert response.primary_structure is None
        assert response.primary_dataset is None
        
        # Test annotation access (should be None for empty structure)
        annotation = response.get_annotation("test")
        assert annotation is None


class TestSDMXDataIntegration:
    """Test integration between different SDMX components."""
    
    def test_full_response_structure(self):
        """Test a complete response structure."""
        # This test verifies that all components work together
        sender = Sender(
            id="STC",
            name="Statistics Canada",
            names={"en": "Statistics Canada", "fr": "Statistique Canada"}
        )
        
        metadata = Metadata(
            schema="2.1.0",
            id="integration-test",
            test=False,
            prepared=datetime.now(),
            sender=sender
        )
        
        # Create structure with annotations
        annotations = [
            Annotation(
                type="NonProductionDataflow",
                text=False,
                texts={"en": "false"}
            )
        ]
        
        structure = Structure(
            name="TestDataStructure",
            names={"en": "Test Data Structure"},
            dimensions=None,  # Would be populated in real scenario
            attributes=None,  # Would be populated in real scenario
            annotations=annotations,
            dataSets=[]
        )
        
        data = Data(
            structures=[structure],
            dataSets=[]
        )
        
        response = SDMXResponse(
            meta=metadata,
            data=data,
            errors=[]
        )
        
        # Verify the complete structure
        assert response.meta.sender.get_display_name("fr") == "Statistique Canada"
        assert response.primary_structure is not None
        assert response.primary_structure.name == "TestDataStructure"
        
        # Test cross-referencing
        annotation = response.get_annotation(False)
        assert annotation is not None
        assert annotation.type == "NonProductionDataflow"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
