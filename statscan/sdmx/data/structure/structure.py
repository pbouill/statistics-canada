from typing import Optional

from statscan.sdmx.data.structure.dimension.series import Series
from statscan.sdmx.data.structure.attributes import Attribute

from ...base import Base
from .attributes import Attributes
from .annotation import Annotation
from .dimensions import Dimensions


class Structure(Base):
    """
    Represents a data structure in SDMX.
    """
    name: str
    names: dict[str, str]  # language -> name mapping
    dimensions: Dimensions
    attributes: Attributes
    annotations: list[Annotation] = []
    dataSets: list = []

    @property
    def annotation_dict(self) -> dict[str | int, Annotation]:
        """Get a dictionary of annotations indexed by their text ID."""
        return {annotation.text: annotation for annotation in self.annotations if annotation.text is not None}

    def get_annotation(self, text: str | int) -> Optional[Annotation]:
        """Get an annotation by its text or ID."""
        for annotation in self.annotations:
            if annotation.text == text:
                return annotation
        return None
    
    def get_display_name(self, language: str = 'en') -> str:
        """Get the display name in the specified lang."""
        return self.names.get(language, self.name)

    # Cross-referencing convenience methods
    def get_series_dimension(self, dimension_id: str) -> Series:
        """Get a series dimension by ID."""
        return self.dimensions[dimension_id]
    
    def get_series_attribute(self, attribute_id: str) -> Attribute:
        """Get a series attribute by ID."""
        return self.attributes[attribute_id]
    
    def cross_reference_annotation(self, annotation_ref: int) -> Optional[Annotation]:
        """Cross-reference an annotation by its reference number."""
        return self.get_annotation(annotation_ref)
    
    def get_dimension_value_by_attribute(self, dimension_id: str, attribute_id: str, value_id: int | str):
        """
        Get a dimension value and its corresponding attribute value.
        Returns a tuple of (dimension_value, attribute_value).
        """
        try:
            dimension = self.dimensions[dimension_id]
            attribute = self.attributes[attribute_id]
            
            dim_value = dimension[value_id]
            attr_value = attribute[value_id] if value_id in [v.id for v in attribute.values] else None
            
            return dim_value, attr_value
        except KeyError:
            return None, None
    
    @property
    def summary(self) -> dict:
        """Get a summary of the structure."""
        return {
            'name': self.name,
            'series_dimensions': len(self.dimensions.series),
            'observation_dimensions': len(self.dimensions.observation),
            'series_attributes': len(self.attributes.series),
            'observation_attributes': len(self.attributes.observation),
            'annotations': len(self.annotations),
            'datasets': len(self.dataSets)
        }