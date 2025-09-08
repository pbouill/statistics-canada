
from typing import Optional, Dict, List
from ...base import Base
from .series import Series


class Link(Base):
    urn: str
    rel: str


class Dataset(Base):
    """
    Represents a dataset in SDMX response.
    Based on actual structure: {structure (int), action (str), links (list), annotations (list), series (dict)}
    """
    structure: int
    action: str
    links: list[Link] = []
    annotations: list[int] = []
    series: dict[str, Series] = {}

    def __getitem__(self, key: str) -> Series:
        """Get a series by its ID."""
        return self.series[key]
    
    def get_series_by_key_parts(self, *key_parts) -> Optional[Series]:
        """Get a series by its key parts (convenience method)."""
        key = ':'.join(str(part) for part in key_parts)
        return self.series.get(key)
    
    def get_all_observations(self) -> Dict[str, Dict[int, List[Optional[float]]]]:
        """Get all observations from all series."""
        return {series_key: series.observations for series_key, series in self.series.items()}
    
    def get_series_keys(self) -> List[str]:
        """Get all series keys."""
        return list(self.series.keys())
    
    def get_total_observations_count(self) -> int:
        """Get total number of observations across all series."""
        return sum(len(series.observations) for series in self.series.values())
    
    @property
    def series_count(self) -> int:
        """Number of series in this dataset."""
        return len(self.series)
    
    def filter_series_by_attributes(self, attribute_values: List[Optional[int]]) -> Dict[str, Series]:
        """
        Filter series by their attribute values.
        
        Args:
            attribute_values: List of attribute values to match
            
        Returns:
            Dictionary of matching series
        """
        filtered = {}
        for key, series in self.series.items():
            if series.attributes == attribute_values:
                filtered[key] = series
        return filtered
    
    def get_series_with_annotations(self, annotation_refs: List[int]) -> Dict[str, Series]:
        """
        Get series that have specific annotation references.
        
        Args:
            annotation_refs: List of annotation reference IDs
            
        Returns:
            Dictionary of matching series
        """
        filtered = {}
        for key, series in self.series.items():
            if any(ref in series.annotations for ref in annotation_refs):
                filtered[key] = series
        return filtered