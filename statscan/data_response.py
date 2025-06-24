"""
Enhanced response handlers for Statistics Canada SDMX data.

This module provides classes to process and transform raw SDMX JSON responses
into more user-friendly formats including pandas DataFrames.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
from dataclasses import dataclass

from statscan.enums.enhanced_stats_filter import Gender, CensusProfileCharacteristic, StatisticType, EnhancedStatsFilter


@dataclass
class DimensionInfo:
    """Information about a single dimension in SDMX data."""
    id: str
    name: str
    values: List[Dict[str, str]]
    
    def get_value_name(self, index: int) -> str:
        """Get the human-readable name for a dimension value by index."""
        if 0 <= index < len(self.values):
            return self.values[index].get('name', f'Unknown_{index}')
        return f'Index_{index}'
    
    def get_value_id(self, index: int) -> str:
        """Get the ID for a dimension value by index."""
        if 0 <= index < len(self.values):
            return self.values[index].get('id', str(index))
        return str(index)


@dataclass 
class SeriesInfo:
    """Information about a data series in SDMX response."""
    key: str
    dimensions: Dict[str, str]  # dimension_name -> value_name
    observations: Dict[str, Union[float, str]]  # time_period -> value
    
    @property
    def dimension_summary(self) -> str:
        """Get a human-readable summary of series dimensions."""
        return " | ".join([f"{k}: {v}" for k, v in self.dimensions.items()])


class CensusDataResponse:
    """
    Enhanced wrapper for Statistics Canada SDMX JSON responses.
    
    Provides automatic dimension decoding, data transformation, and
    convenient access methods.
    """
    
    def __init__(self, raw_response: Dict[str, Any]):
        """
        Initialize with raw SDMX JSON response.
        
        Args:
            raw_response: The raw JSON response from Statistics Canada API
        """
        self.raw_response = raw_response
        self._dimensions: Optional[Dict[str, DimensionInfo]] = None
        self._series_info: Optional[List[SeriesInfo]] = None
        
    @property
    def dimensions(self) -> Dict[str, DimensionInfo]:
        """Get parsed dimension information."""
        if self._dimensions is None:
            self._parse_dimensions()
        return self._dimensions or {}
    
    @property
    def series_info(self) -> List[SeriesInfo]:
        """Get parsed series information with decoded dimensions."""
        if self._series_info is None:
            self._parse_series()
        return self._series_info or []
    
    def _parse_dimensions(self) -> None:
        """Parse dimension information from raw response."""
        self._dimensions = {}
        
        # Try different possible locations for dimensions in SDMX structure
        structures = None
        if 'data' in self.raw_response:
            if 'structures' in self.raw_response['data']:
                structures = self.raw_response['data']['structures']
            
        if structures and len(structures) > 0:
            dims = structures[0].get('dimensions', {})
            if 'series' in dims:
                for i, dim in enumerate(dims['series']):
                    dim_id = dim.get('id', f'dim_{i}')
                    dim_name = dim.get('name', dim_id)
                    dim_values = dim.get('values', [])
                    
                    self._dimensions[dim_name] = DimensionInfo(
                        id=dim_id,
                        name=dim_name,
                        values=dim_values
                    )
    
    def _parse_series(self) -> None:
        """Parse series data with decoded dimensions."""
        self._series_info = []
        
        if 'data' in self.raw_response and 'dataSets' in self.raw_response['data']:
            datasets = self.raw_response['data']['dataSets']
            if len(datasets) > 0 and 'series' in datasets[0]:
                series_data = datasets[0]['series']
                
                for series_key, series_values in series_data.items():
                    # Decode series key using dimensions
                    dimensions = self._decode_series_key(series_key)
                    
                    # Extract observations
                    observations = series_values.get('observations', {})
                    
                    self._series_info.append(SeriesInfo(
                        key=series_key,
                        dimensions=dimensions,
                        observations=observations
                    ))
    
    def _decode_series_key(self, series_key: str) -> Dict[str, str]:
        """Decode a series key using dimension information."""
        decoded = {}
        key_parts = series_key.split(':')
        
        dim_names = list(self.dimensions.keys())
        for i, part_idx in enumerate(key_parts):
            if i < len(dim_names):
                dim_name = dim_names[i]
                dim_info = self.dimensions[dim_name]
                try:
                    idx = int(part_idx)
                    decoded[dim_name] = dim_info.get_value_name(idx)
                except (ValueError, IndexError):
                    decoded[dim_name] = part_idx
        
        return decoded
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the response to a pandas DataFrame.
        
        Returns:
            DataFrame with columns for each dimension plus time periods and values
        """
        rows = []
        
        for series in self.series_info:
            base_row = series.dimensions.copy()
            base_row['series_key'] = series.key
            
            for time_period, value in series.observations.items():
                row = base_row.copy()
                row['time_period'] = time_period
                row['value'] = value
                rows.append(row)
        
        return pd.DataFrame(rows)
    
    def filter_series(self, 
                     gender: Optional[str] = None,
                     characteristic: Optional[str] = None,
                     statistic_type: Optional[str] = None) -> List[SeriesInfo]:
        """
        Filter series by dimension values.
        
        Args:
            gender: Filter by gender dimension
            characteristic: Filter by characteristic dimension  
            statistic_type: Filter by statistic type dimension
            
        Returns:
            List of SeriesInfo matching the filters
        """
        filtered = []
        
        for series in self.series_info:
            matches = True
            
            if gender and series.dimensions.get('Gender', '').lower() != gender.lower():
                matches = False
            if characteristic and characteristic.lower() not in series.dimensions.get('Census Profile Characteristic', '').lower():
                matches = False
            if statistic_type and series.dimensions.get('Statistic Type', '').lower() != statistic_type.lower():
                matches = False
                
            if matches:
                filtered.append(series)
        
        return filtered

    def filter_by_enhanced_filter(self, enhanced_filter: EnhancedStatsFilter) -> List[SeriesInfo]:
        """
        Filter series using EnhancedStatsFilter enum values.
        
        Args:
            enhanced_filter: EnhancedStatsFilter with enum-based filtering
            
        Returns:
            List of SeriesInfo matching the enhanced filter
        """
        filtered = []
        
        for series in self.series_info:
            matches = True
            
            # Check gender filter
            if enhanced_filter.gender:
                gender_name = enhanced_filter.gender.name.replace('_', ' ').title()
                series_gender = series.dimensions.get('Gender', '')
                if gender_name.lower() not in series_gender.lower():
                    matches = False
            
            # Check characteristic filter
            if enhanced_filter.census_profile_characteristic:
                char_name = enhanced_filter.census_profile_characteristic.name.replace('_', ' ').title()
                series_char = series.dimensions.get('Census Profile Characteristic', '')
                if char_name.lower() not in series_char.lower():
                    matches = False
            
            # Check statistic type filter
            if enhanced_filter.statistic_type:
                stat_name = enhanced_filter.statistic_type.name.replace('_', ' ').title()
                series_stat = series.dimensions.get('Statistic Type', '')
                if stat_name.lower() not in series_stat.lower():
                    matches = False
            
            if matches:
                filtered.append(series)
        
        return filtered

    def get_characteristics_by_category(self) -> Dict[str, List[str]]:
        """
        Group available characteristics by category.
        
        Returns:
            Dict mapping category names to lists of characteristics
        """
        characteristics = {}
        
        for series in self.series_info:
            char = series.dimensions.get('Census Profile Characteristic', '')
            if char:
                # Try to match with known enum values to get category
                category = "Other"
                for enum_char in CensusProfileCharacteristic:
                    if enum_char.name.replace('_', ' ').lower() in char.lower():
                        category = enum_char.category
                        break
                
                if category not in characteristics:
                    characteristics[category] = []
                if char not in characteristics[category]:
                    characteristics[category].append(char)
        
        return characteristics
    


class CensusDataFrame(pd.DataFrame):
    """
    Enhanced pandas DataFrame for Statistics Canada census data.
    
    Provides additional methods specific to census data analysis.
    """
    
    def __init__(self, data=None, **kwargs):
        super().__init__(data, **kwargs)
    
    @property
    def _constructor(self):
        return CensusDataFrame
    
    def filter_by_gender(self, gender: str) -> 'CensusDataFrame':
        """Filter data by gender."""
        if 'Gender' in self.columns:
            return self[self['Gender'].str.contains(gender, case=False, na=False)]
        return self
    
    def filter_by_characteristic(self, characteristic: str) -> 'CensusDataFrame':
        """Filter data by census characteristic."""
        char_cols = [col for col in self.columns if 'characteristic' in col.lower()]
        if char_cols:
            col = char_cols[0]
            return self[self[col].str.contains(characteristic, case=False, na=False)]
        return self
    
    def get_population_data(self) -> 'CensusDataFrame':
        """Get only population-related data."""
        return self.filter_by_characteristic('population')
    
    def get_age_data(self) -> 'CensusDataFrame':
        """Get only age-related data.""" 
        return self.filter_by_characteristic('age')
    
    def get_household_data(self) -> 'CensusDataFrame':
        """Get only household-related data."""
        return self.filter_by_characteristic('household')
    
    def pivot_by_gender(self) -> pd.DataFrame:
        """Pivot data to show gender breakdown by characteristic."""
        if 'Gender' in self.columns and 'value' in self.columns:
            char_col = next((col for col in self.columns if 'characteristic' in col.lower()), None)
            if char_col:
                return self.pivot_table(
                    index=char_col,
                    columns='Gender', 
                    values='value',
                    aggfunc='first'
                )
        return pd.DataFrame()
    
    def summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for numeric columns."""
        numeric_cols = self.select_dtypes(include=['number']).columns
        return {
            'shape': self.shape,
            'numeric_columns': list(numeric_cols),
            'non_null_counts': self.count().to_dict(),
            'value_ranges': {col: {'min': self[col].min(), 'max': self[col].max()} 
                           for col in numeric_cols if col in self.columns}
        }

    def filter_by_enum(self, 
                      gender: Optional[Gender] = None,
                      characteristic: Optional[CensusProfileCharacteristic] = None,
                      statistic_type: Optional[StatisticType] = None) -> 'CensusDataFrame':
        """
        Filter data using enhanced enum values.
        
        Args:
            gender: Gender enum value to filter by
            characteristic: CensusProfileCharacteristic enum to filter by
            statistic_type: StatisticType enum to filter by
            
        Returns:
            Filtered CensusDataFrame
        """
        df = self.copy()
        
        if gender:
            gender_name = gender.name.replace('_', ' ').title()
            if 'Gender' in df.columns:
                df = df[df['Gender'].str.contains(gender_name, case=False, na=False)]
        
        if characteristic:
            char_name = characteristic.name.replace('_', ' ').title()
            char_cols = [col for col in df.columns if 'characteristic' in col.lower()]
            if char_cols:
                df = df[df[char_cols[0]].str.contains(char_name, case=False, na=False)]
        
        if statistic_type:
            stat_name = statistic_type.name.replace('_', ' ').title()
            stat_cols = [col for col in df.columns if 'statistic' in col.lower()]
            if stat_cols:
                df = df[df[stat_cols[0]].str.contains(stat_name, case=False, na=False)]
        
        return df

    def get_income_data(self) -> 'CensusDataFrame':
        """Get income-related data."""
        income_terms = ['income', 'earning', 'wage', 'salary']
        char_cols = [col for col in self.columns if 'characteristic' in col.lower()]
        if char_cols:
            mask = self[char_cols[0]].str.contains('|'.join(income_terms), case=False, na=False)
            return self[mask]
        return self

    def get_education_data(self) -> 'CensusDataFrame':
        """Get education-related data."""
        education_terms = ['education', 'school', 'degree', 'diploma', 'certificate']
        char_cols = [col for col in self.columns if 'characteristic' in col.lower()]
        if char_cols:
            mask = self[char_cols[0]].str.contains('|'.join(education_terms), case=False, na=False)
            return self[mask]
        return self

    def get_employment_data(self) -> 'CensusDataFrame':
        """Get employment-related data."""
        employment_terms = ['employment', 'labour', 'work', 'job', 'occupation']
        char_cols = [col for col in self.columns if 'characteristic' in col.lower()]
        if char_cols:
            mask = self[char_cols[0]].str.contains('|'.join(employment_terms), case=False, na=False)
            return self[mask]
        return self

    def get_dwelling_data(self) -> 'CensusDataFrame':
        """Get dwelling and housing-related data."""
        dwelling_terms = ['dwelling', 'housing', 'house', 'apartment', 'home']
        char_cols = [col for col in self.columns if 'characteristic' in col.lower()]
        if char_cols:
            mask = self[char_cols[0]].str.contains('|'.join(dwelling_terms), case=False, na=False)
            return self[mask]
        return self

    def compare_by_gender(self) -> pd.DataFrame:
        """Create a comparison table by gender for key characteristics."""
        char_col = next((col for col in self.columns if 'characteristic' in col.lower()), None)
        gender_col = 'Gender' if 'Gender' in self.columns else None
        
        if char_col and gender_col and 'value' in self.columns:
            # Get latest values only
            latest = self.loc[self.groupby(['series_key'])['time_period'].idxmax()] if 'time_period' in self.columns else self
            
            # Pivot to compare by gender
            comparison = latest.pivot_table(
                index=char_col,
                columns=gender_col,
                values='value',
                aggfunc='first'
            )
            
            # Calculate gender ratio if both male and female are present
            if 'Male' in comparison.columns and 'Female' in comparison.columns:
                comparison['Male_to_Female_Ratio'] = comparison['Male'] / comparison['Female']
            
            return comparison
        
        return pd.DataFrame()

    def get_top_characteristics(self, n: int = 10, by_value: bool = True) -> 'CensusDataFrame':
        """
        Get the top N characteristics by value or other criteria.
        
        Args:
            n: Number of top characteristics to return
            by_value: Sort by value (True) or alphabetically (False)
            
        Returns:
            CensusDataFrame with top characteristics
        """
        if 'value' not in self.columns:
            return self.head(n)
        
        # Get latest values
        latest = self.loc[self.groupby(['series_key'])['time_period'].idxmax()] if 'time_period' in self.columns else self
        
        if by_value:
            # Sort by value (handle NaN and non-numeric values)
            numeric_mask = pd.to_numeric(latest['value'], errors='coerce').notna()
            numeric_data = latest[numeric_mask].copy()
            numeric_data['value_numeric'] = pd.to_numeric(numeric_data['value'])
            top_data = numeric_data.nlargest(n, 'value_numeric')
        else:
            # Sort alphabetically by characteristic
            char_col = next((col for col in self.columns if 'characteristic' in col.lower()), None)
            if char_col:
                top_data = latest.sort_values(char_col).head(n)
            else:
                top_data = latest.head(n)
        
        return top_data
