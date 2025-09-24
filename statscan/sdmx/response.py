from typing import Optional, Any
import pandas as pd
import logging

from statscan.sdmx.data.dataset.dataset import Dataset
from statscan.sdmx.data.structure.structure import Structure
from .base import Base
from .meta import Metadata
from .data.data import Data
from .data.structure.annotation import Annotation
from .data.structure.dimension.series import Series as SeriesDimension
from .data.structure.attributes import Attribute
from .data.dataset.series import Series as DatasetSeries


logger = logging.getLogger(__name__)

class SDMXResponse(Base):
    """
    Represents a response from an SDMX data request.
    
    Provides access to metadata, data structures, dimensions, attributes,
    and convenience methods for cross-referencing annotations and values.
    """
    meta: Metadata
    data: Data
    errors: list = []
    _raw_data: Optional[dict[str, Any]] = None

    @property
    def structures(self) -> list[Structure]:
        """Get the list of data structures."""
        return self.data.structures
    
    @property
    def datasets(self) -> list[Dataset]:
        """Get the list of datasets."""
        return self.data.dataSets

    def get_annotation(self, annotation_ref: str | int | bool, structure: Optional[Structure] = None) -> Optional[Annotation]:
        """
        Cross-reference an annotation by its reference ID, text, or boolean value.
        
        Args:
            annotation_ref: The annotation reference (ID, text, or boolean value)
            structure: The data structure to search within (uses primary if None)

        Returns:
            The annotation if found, None otherwise
        """
        if structure is None:
            structure = self.primary_structure
        
        if not structure or not hasattr(structure, 'annotations') or structure.annotations is None:
            return None
        
        # Boolean lookup
        if isinstance(annotation_ref, bool):
            for a in structure.annotations:
                if getattr(a, 'text', None) == annotation_ref:
                    return a
            return None
        # String/int lookup directly
        for a in structure.annotations:
            if getattr(a, 'text', None) == annotation_ref:
                return a
        return None

    def get_annotations_by_type(self, annotation_type: str) -> list[Annotation]:
        """
        Get annotations of a specific type from the primary structure.
        
        Args:
            annotation_type: The type of annotation to search for

        Returns:
            List of annotations matching the specified type
        """
        structure = self.primary_structure
        matches: list[Annotation] = []
        if not structure:
            return matches
        if hasattr(structure, 'annotations'):
            for a in structure.annotations:
                if getattr(a, 'type', None) == annotation_type:
                    matches.append(a)
        if hasattr(structure, 'dimensions') and hasattr(structure.dimensions, 'series'):
            for dim in structure.dimensions.series:
                if (annotations := getattr(dim, 'annotations', None)) is not None:
                    for a in annotations:
                        if getattr(a, 'type', None) == annotation_type:
                            matches.append(a)
        if hasattr(structure, 'attributes'):
            for attr_list in (getattr(structure.attributes, 'series', []), getattr(structure.attributes, 'observation', [])):
                for attr in attr_list:
                    if hasattr(attr, 'annotations'):
                        for a in attr.annotations:
                            if getattr(a, 'type', None) == annotation_type:
                                matches.append(a)
        return matches

    @property
    def primary_structure(self) -> Optional[Structure]:
        """Get the primary (first) data structure."""
        if self.structures:
            return self.structures[0]
        return None
    
    @property
    def primary_dataset(self) -> Optional[Dataset]:
        """Get the primary (first) dataset."""
        if self.datasets:
            return self.datasets[0]
        return None

    def get_dimension_summary(self) -> dict[str, dict]:
        """
        Get a summary of all dimensions and their value counts.
        
        Returns:
            Dictionary with dimension summaries
        """
        structure = self.primary_structure
        if not structure or not getattr(structure, 'dimensions', None) or not getattr(structure.dimensions, 'series', None):
            return {}
        summary = {}
        for dim in structure.dimensions.series:
            values = getattr(dim, 'values', []) or []
            summary[dim.id] = {
                'name': getattr(dim, 'name', dim.id),
                'display_name': dim.get_display_name() if hasattr(dim, 'get_display_name') else getattr(dim, 'name', dim.id),
                'value_count': len(values),
                'key_position': getattr(dim, 'keyPosition', None),
                'roles': getattr(dim, 'roles', []) or [],
                'sample_values': [getattr(v, 'name', str(getattr(v, 'id', ''))) for v in values[:3]]
            }
        return summary

    def cross_reference_dimension_attribute(self, dimension_id: str, attribute_id: str, value_id: int | str):
        """
        Cross-reference a dimension value with its corresponding attribute value.
        
        Args:
            dimension_id: The dimension ID
            attribute_id: The attribute ID  
            value_id: The value ID to look up
            
        Returns:
            Tuple of (dimension_value, attribute_value) or (None, None) if not found
        """
        structure = self.primary_structure
        if not structure:
            return None, None
        return structure.get_dimension_value_by_attribute(dimension_id, attribute_id, value_id) if hasattr(structure, 'get_dimension_value_by_attribute') else (None, None)

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the SDMX response to a pandas DataFrame.
        
        Returns:
            DataFrame with decoded dimension names as columns, plus 
            time periods and values
        """
        if not self._raw_data:
            return pd.DataFrame()
        
        data_rows = []
        
        # Try to extract data from the raw SDMX response
        try:
            # Look for data in the typical SDMX structure
            data_section = self.data
            structures = data_section.structures
            datasets = data_section.dataSets
            
            if not structures or not datasets:
                return pd.DataFrame()
            
            structure = structures[0]  # Use first structure
            dataset = datasets[0]  # Use first dataset
            
            # Extract dimension information
            dimensions = {}
            if hasattr(structure, 'dimensions') and hasattr(structure.dimensions, 'series'):
                for i, dim in enumerate(structure.dimensions.series):
                    dimensions[i] = {
                        'id': getattr(dim, 'id', f'dim_{i}'),
                        'name': getattr(dim, 'name', f'Dimension {i}'),
                        'values': getattr(dim, 'values', [])
                    }
            
            # Extract series data
            if hasattr(dataset, 'series'):
                for series_key, series_data in dataset.series.items():
                    # Decode series key
                    dimension_values = {}
                    key_parts = series_key.split(':')
                    
                    for i, part in enumerate(key_parts):
                        if i in dimensions:
                            dim_info = dimensions[i]
                            try:
                                value_index = int(part)
                                if 0 <= value_index < len(dim_info['values']):
                                    value_info = dim_info['values'][value_index]
                                    dimension_values[dim_info['name']] = getattr(value_info, 'name', f'Value_{value_index}')
                            except (ValueError, IndexError):
                                dimension_values[dim_info.get('name', f'dim_{i}')] = part
                    
                    # Extract observations
                    if hasattr(series_data, 'observations'):
                        for obs_key, obs_value in series_data.observations.items():
                            row = {
                                'series_key': series_key,
                                'time_period': obs_key,
                                'value': obs_value[0] if isinstance(obs_value, list) else obs_value,
                                **dimension_values
                            }
                            data_rows.append(row)
            
        except Exception as e:
            # If parsing fails, return empty DataFrame
            logger.warning(f"Failed to parse SDMX response: {e}")
            return pd.DataFrame()
        
        return pd.DataFrame(data_rows)
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """
        Get the response data as a pandas DataFrame.
        
        Returns:
            DataFrame representation of the SDMX response
        """
        return self.to_dataframe().pipe(self._standardize_dataframe)
    
    # --- New helper methods ---
    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column naming and value normalization for downstream tests.
        - Rename 'value' -> 'Value'
        - Identify & rename probable Gender column
        - Identify & rename characteristic/measure column as 'Characteristic'
        - Ensure numeric conversion of Value
        """
        if df.empty:
            return df
        df = df.copy()
        # Standardize value column
        if 'value' in df.columns and 'Value' not in df.columns:
            df = df.rename(columns={'value': 'Value'})
        if 'Value' in df.columns:
            try:
                df['Value'] = pd.to_numeric(df['Value'])
            except Exception as e:
                logger.warning(f"Failed to convert 'Value' column to numeric: {e}")
        # Identify gender-like column
        gender_markers = {'men', 'women', 'gender', 'male', 'female'}
        if 'Gender' not in df.columns:
            for col in df.columns:
                if col in {'series_key', 'time_period', 'Value'}:
                    continue
                sample_vals = df[col].astype(str).str.lower()
                if sample_vals.isin(['total - gender', 'total']).any() or sample_vals.str.contains('|'.join(gender_markers), na=False).any():
                    df = df.rename(columns={col: 'Gender'})
                    break
        # Normalize gender labels
        if 'Gender' in df.columns:
            df['Gender'] = (df['Gender']
                              .replace({'Total': 'Total - Gender',
                                         'Total - sex': 'Total - Gender',
                                         'Both sexes': 'Total - Gender'})
                              .fillna(df['Gender']))
        # Identify characteristic column
        if 'Characteristic' not in df.columns:
            characteristic_terms = ['population', 'dwellings', 'age', 'density', 'land area', 'percentage change', 'income']
            candidate_scores: list[tuple[str,int]] = []
            for col in df.columns:
                if col in {'series_key', 'time_period', 'Value', 'Gender'}:
                    continue
                col_vals = df[col].astype(str).str.lower()
                score = sum(col_vals.str.contains(term, na=False).sum() for term in characteristic_terms)
                if score:
                    candidate_scores.append((col, score))
            if candidate_scores:
                best_col = sorted(candidate_scores, key=lambda x: x[1], reverse=True)[0][0]
                df = df.rename(columns={best_col: 'Characteristic'})
        # Drop NaN population rows if numeric exists
        if {'Characteristic', 'Gender', 'Value'}.issubset(df.columns):
            pop_mask = df['Characteristic'].astype(str).str.contains('Population, 2021', case=False, na=False)
            if pop_mask.any():
                pop_rows = df[pop_mask]
                if pop_rows['Value'].notna().any() and pop_rows['Value'].isna().any():
                    keep_idx = pop_rows[pop_rows['Value'].notna()].index
                    df = df[~pop_mask | df.index.isin(keep_idx)]
        # Column ordering for user-friendliness
        preferred_order = [c for c in ['Reference area', 'Characteristic', 'Gender', 'Value', 'Statistic', 'Frequency', 'time_period', 'series_key'] if c in df.columns]
        other_cols = [c for c in df.columns if c not in preferred_order]
        df = df[preferred_order + other_cols]
        return df
    
    def get_population_data(self) -> pd.DataFrame:
        """
        Filter for population-related data.
        
        Returns:
            DataFrame containing only population data
        """
        df = self.dataframe
        if df.empty:
            return df
        # Prefer explicit Characteristic column
        if 'Characteristic' in df.columns:
            mask = df['Characteristic'].astype(str).str.lower().str.contains('population')
            if mask.any():
                return df[mask]
        population_terms = ['population', 'total', 'pop']
        population_mask = pd.Series(False, index=df.index)
        for col in df.columns:
            if col not in ['series_key', 'time_period', 'Value']:
                col_mask = df[col].astype(str).str.lower().str.contains('|'.join(population_terms), na=False)
                population_mask |= col_mask
        return df[population_mask]
    
    def get_age_demographics(self) -> pd.DataFrame:
        """
        Filter for age-related demographic data.
        
        Returns:
            DataFrame containing age demographic data
        """
        df = self.dataframe
        if df.empty:
            return df
        if 'Characteristic' in df.columns:
            mask = df['Characteristic'].astype(str).str.lower().str.contains('age')
            if mask.any():
                return df[mask]
        age_terms = ['age', 'years', 'year old', 'demographic']
        age_mask = pd.Series(False, index=df.index)
        for col in df.columns:
            if col not in ['series_key', 'time_period', 'Value']:
                col_mask = df[col].astype(str).str.lower().str.contains('|'.join(age_terms), na=False)
                age_mask |= col_mask
        return df[age_mask]
    
    def get_household_statistics(self) -> pd.DataFrame:
        """
        Filter for household-related statistics.
        
        Returns:
            DataFrame containing household statistics
        """
        df = self.dataframe
        if df.empty:
            return df
        if 'Characteristic' in df.columns:
            mask = df['Characteristic'].astype(str).str.lower().str.contains('household|dwelling|private|housing')
            if mask.any():
                return df[mask]
        household_terms = ['household', 'dwelling', 'private', 'occupied', 'housing']
        household_mask = pd.Series(False, index=df.index)
        for col in df.columns:
            if col not in ['series_key', 'time_period', 'Value']:
                col_mask = df[col].astype(str).str.lower().str.contains('|'.join(household_terms), na=False)
                household_mask |= col_mask
        return df[household_mask]
    
    def get_series_dimension(self, dimension_id: str) -> Optional[SeriesDimension]:
        """
        Get a series dimension by its ID.
        
        Args:
            dimension_id: The ID of the dimension
            
        Returns:
            The series dimension if found, None otherwise
        """
        structure = self.primary_structure
        if not structure:
            return None
        
        if hasattr(structure, 'dimensions') and hasattr(structure.dimensions, 'series'):
            for dim in structure.dimensions.series:
                if getattr(dim, 'id', None) == dimension_id:
                    return dim
        return None

    def get_series_attribute(self, attribute_id: str) -> Optional[Attribute]:
        """
        Get a series attribute by its ID.
        
        Args:
            attribute_id: The ID of the attribute
            
        Returns:
            The series attribute if found, None otherwise
        """
        structure = self.primary_structure
        if not structure:
            return None
        
        if hasattr(structure, 'attributes') and hasattr(structure.attributes, 'series'):
            for attr in structure.attributes.series:
                if getattr(attr, 'id', None) == attribute_id:
                    return attr
        return None

    def get_dataset_series(self, series_key: str) -> Optional[DatasetSeries]:
        """
        Get a dataset series by its key.
        
        Args:
            series_key: The series key
            
        Returns:
            The dataset series if found, None otherwise
        """
        dataset = self.primary_dataset
        if not dataset:
            return None
        
        if hasattr(dataset, 'series'):
            return dataset.series.get(series_key)
        return None
    
    def get_attribute_summary(self) -> dict[str, dict]:
        """
        Get a summary of all attributes and their properties.
        
        Returns:
            Dictionary with attribute summaries
        """
        structure = self.primary_structure
        if not structure or not getattr(structure, 'attributes', None):
            return {}
        summary: dict[str, dict] = {}
        for attr_list, atype in ((getattr(structure.attributes, 'series', []) or [], 'series'), (getattr(structure.attributes, 'observation', []) or [], 'observation')):
            for attr in attr_list:
                values = getattr(attr, 'values', []) or []
                summary[attr.id] = {
                    'name': getattr(attr, 'name', attr.id),
                    'usage_status': getattr(attr, 'usage_status', None),
                    'roles': getattr(attr, 'roles', []) or [],
                    'type': atype,
                    'value_count': len(values)
                }
        return summary
    
    # --- Added/extended methods for enhanced tests ---
    def search_values(self, query: str, case: bool = False) -> dict[str, list[str]]:
        """Search dimension and attribute values containing a query string.
        Returns dict with 'dimensions' and 'attributes' lists of matches."""
        results: dict[str, list[str]] = {"dimensions": [], "attributes": []}
        structure = self.primary_structure
        if not structure:
            return results
        q = query if case else query.lower()
        # Search dimension values
        if hasattr(structure, 'dimensions') and hasattr(structure.dimensions, 'series'):
            for dim in structure.dimensions.series:
                for val in getattr(dim, 'values', []):
                    name = getattr(val, 'name', '') or ''
                    hay = name if case else name.lower()
                    if q in hay:
                        results['dimensions'].append(name)
        # Search attribute values
        if hasattr(structure, 'attributes'):
            for attr_collection in (getattr(structure.attributes, 'series', []), getattr(structure.attributes, 'observation', [])):
                for attr in attr_collection:
                    for val in getattr(attr, 'values', []):
                        name = getattr(val, 'name', '') or ''
                        hay = name if case else name.lower()
                        if q in hay:
                            results['attributes'].append(name)
        return results
    
    @property
    def response_summary(self) -> dict[str, Any]:
        """Aggregate high-level summary of response for tests."""
        meta = {
            'id': getattr(self.meta, 'id', None),
            'prepared': getattr(self.meta, 'prepared', None),
            'test': getattr(self.meta, 'test', None)
        }
        dataset_info = {}
        primary_dataset = self.primary_dataset
        if primary_dataset is not None:
            dataset_info = {
                'series_count': len(getattr(primary_dataset, 'series', {})),
                'total_observations': sum(len(s.observations) for s in primary_dataset.series.values()) if getattr(primary_dataset, 'series', None) else 0
            }
        return {
            'meta': meta,
            'dataset': dataset_info,
            'dimensions': list(self.get_dimension_summary().keys()),
            'attributes': list(self.get_attribute_summary().keys())
        }
