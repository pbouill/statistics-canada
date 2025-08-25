"""
Enhanced response handlers for Statistics Canada SDMX data.

This module provides classes to process and transform raw SDMX JSON responses
into more user-friendly formats including pandas DataFrames.

.. deprecated:: 
    This module is deprecated and will be removed in a future version.
    Use statscan.sdmx.response.SDMXResponse instead.
"""

import warnings
from typing import Any, Optional, ClassVar, Self
from datetime import datetime

from dataclasses import dataclass

import pandas as pd

from statscan.enums.stats_filter import Gender, CensusProfileCharacteristic, StatisticType, StatsFilter, CommonFilters

# Deprecation warning
warnings.warn(
    "census_data module is deprecated and will be removed in a future version. "
    "Use statscan.sdmx.response.SDMXResponse instead.",
    DeprecationWarning,
    stacklevel=2
)



@dataclass
class DimensionInfo:
    """Information about a single dimension in SDMX data."""
    id: str
    name: str
    values: list[dict[str, str]]
    
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
    dimensions: dict[str, str]  # dimension_name -> value_name
    observations: dict[str, float | str]  # time_period -> value
    
    @property
    def dimension_summary(self) -> str:
        """Get a human-readable summary of series dimensions."""
        return " | ".join([f"{k}: {v}" for k, v in self.dimensions.items()])


class CensusData:
    """
    Enhanced wrapper for Statistics Canada SDMX JSON responses.
    
    Provides automatic dimension decoding, data transformation, and
    convenient access methods. Data is stored as a DataFrame for
    optimal performance.
    """

    COMMON_FILTERS: ClassVar[type] = CommonFilters
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize with a DataFrame containing census data.
        
        Args:
            dataframe: The DataFrame containing all census data with columns for
                      dimensions, series_key, time_period, and value
        """
        self._dataframe = dataframe
    
    @property
    def dataframe(self) -> pd.DataFrame:
        """
        Get the enhanced DataFrame with meaningful dimension columns.
        
        Returns:
            DataFrame with decoded dimension names as columns, plus dimension 
            components for reference, time periods, and values
        """
        return self._dataframe
    
    @property
    def dimensions(self) -> dict[str, DimensionInfo]:
        """Extract dimension information from the DataFrame."""
        dimensions = {}
        
        # Get all dimension columns (exclude metadata columns)
        metadata_cols = {'series_key', 'time_period', 'value'}
        dimension_cols = [col for col in self._dataframe.columns if col not in metadata_cols]
        
        for col in dimension_cols:
            unique_values = self._dataframe[col].dropna().unique()
            values = []
            for i, value in enumerate(unique_values):
                values.append({'id': str(i), 'name': str(value)})
            
            dimensions[col] = DimensionInfo(
                id=col.lower().replace(' ', '_'),
                name=col,
                values=values
            )
        
        return dimensions
    
    @property
    def series_info(self) -> list[SeriesInfo]:
        """Extract series information from the DataFrame."""
        series_list: list[SeriesInfo] = []
        
        if 'series_key' not in self._dataframe.columns:
            return series_list
        
        # Group by series_key to get observations for each series
        metadata_cols = {'series_key', 'time_period', 'value'}
        dimension_cols = [col for col in self._dataframe.columns if col not in metadata_cols]
        
        for series_key, group in self._dataframe.groupby('series_key'):
            # Get dimensions for this series (should be consistent within a series)
            dimensions = {}
            if not group.empty:
                first_row = group.iloc[0]
                for col in dimension_cols:
                    if pd.notna(first_row[col]):
                        dimensions[col] = str(first_row[col])
            
            # Get observations (time_period -> value mapping)
            observations = {}
            if 'time_period' in group.columns and 'value' in group.columns:
                for _, row in group.iterrows():
                    if pd.notna(row['time_period']) and pd.notna(row['value']):
                        observations[str(row['time_period'])] = row['value']
            
            series_list.append(SeriesInfo(
                key=str(series_key),
                dimensions=dimensions,
                observations=observations
            ))
        
        return series_list
    
    @classmethod
    def from_raw_response(cls, raw_response: dict[str, Any]) -> 'CensusData':
        """
        Create a CensusData instance from a raw SDMX JSON response.
        
        Args:
            raw_response: The raw JSON response from Statistics Canada API
            
        Returns:
            CensusData instance with parsed data
        """
        # Parse dimensions
        dimensions = cls._parse_dimensions(raw_response)
        
        # Parse series data
        series_info = cls._parse_series(raw_response, dimensions)
        
        # Create DataFrame
        dataframe = cls._create_dataframe(series_info)
        
        return cls(dataframe)
    
    @staticmethod
    def _parse_dimensions(raw_response: dict[str, Any]) -> dict[str, DimensionInfo]:
        """Parse dimension information from raw response."""
        dimensions = {}
        
        # Try different possible locations for dimensions in SDMX structure
        structures = None
        if 'data' in raw_response:
            if 'structures' in raw_response['data']:
                structures = raw_response['data']['structures']
            
        if structures and len(structures) > 0:
            dims = structures[0].get('dimensions', {})
            if 'series' in dims:
                for i, dim in enumerate(dims['series']):
                    dim_id = dim.get('id', f'dim_{i}')
                    dim_name = dim.get('name', dim_id)
                    dim_values = dim.get('values', [])
                    
                    dimensions[dim_name] = DimensionInfo(
                        id=dim_id,
                        name=dim_name,
                        values=dim_values
                    )
        
        return dimensions
    
    @staticmethod
    def _parse_series(raw_response: dict[str, Any], dimensions: dict[str, DimensionInfo]) -> list[SeriesInfo]:
        """Parse series data with decoded dimensions."""
        series_info = []
        
        if 'data' in raw_response and 'dataSets' in raw_response['data']:
            datasets = raw_response['data']['dataSets']
            if len(datasets) > 0 and 'series' in datasets[0]:
                series_data = datasets[0]['series']
                
                for series_key, series_values in series_data.items():
                    # Decode series key using dimensions
                    decoded_dimensions = CensusData._decode_series_key(series_key, dimensions)
                    
                    # Extract observations
                    observations = series_values.get('observations', {})
                    
                    series_info.append(SeriesInfo(
                        key=series_key,
                        dimensions=decoded_dimensions,
                        observations=observations
                    ))
        
        return series_info
    
    @staticmethod
    def _decode_series_key(series_key: str, dimensions: dict[str, DimensionInfo]) -> dict[str, str]:
        """Decode a series key using dimension information and map to enum values when possible."""
        decoded = {}
        key_parts = series_key.split(':')
        
        dim_names = list(dimensions.keys())
        for i, part_idx in enumerate(key_parts):
            if i < len(dim_names):
                dim_name = dim_names[i]
                dim_info = dimensions[dim_name]
                try:
                    idx = int(part_idx)
                    human_readable_value = dim_info.get_value_name(idx)
                    
                    # Try to map to enum values for key dimensions
                    enum_value = CensusData._map_to_enum_value(dim_name, human_readable_value)
                    decoded[dim_name] = enum_value if enum_value is not None else human_readable_value
                    
                except (ValueError, IndexError):
                    decoded[dim_name] = part_idx
        
        return decoded
    
    @staticmethod
    def _map_to_enum_value(dimension_name: str, human_readable_value: str) -> Optional[Any]:
        """Map human-readable dimension values to enum values when possible."""
        if not human_readable_value:
            return None
        
        value_lower = human_readable_value.lower()
        
        # Map Gender dimension
        if 'gender' in dimension_name.lower():
            if ('total' in value_lower or 'both' in value_lower or 'all' in value_lower or 
                'men+' in value_lower or 'women+' in value_lower or 'persons' in value_lower):
                return Gender.TOTAL_GENDER
            elif ('male' in value_lower or 'men' in value_lower) and 'female' not in value_lower:
                return Gender.MALE
            elif 'female' in value_lower or 'women' in value_lower:
                return Gender.FEMALE
        
        # Map Statistic dimension
        elif 'statistic' in dimension_name.lower():
            if 'count' in value_lower or 'number' in value_lower or 'counts' in value_lower:
                return StatisticType.COUNT
            elif 'percentage' in value_lower or 'percent' in value_lower:
                return StatisticType.PERCENTAGE
            elif 'rate' in value_lower or 'rates' in value_lower:
                return StatisticType.RATE
            elif 'median' in value_lower:
                return StatisticType.MEDIAN
            elif 'average' in value_lower or 'mean' in value_lower:
                return StatisticType.AVERAGE
            elif 'ratio' in value_lower:
                return StatisticType.RATIO
            elif 'index' in value_lower:
                return StatisticType.INDEX
        
        # Map Census Profile Characteristic dimension (basic mapping for common ones)
        elif 'characteristic' in dimension_name.lower():
            if ('population' in value_lower and 'density' not in value_lower and 
                ('total' in value_lower or 'count' in value_lower or value_lower.strip() == 'population')):
                return CensusProfileCharacteristic.POPULATION_COUNT
            elif 'population density' in value_lower or 'density per' in value_lower:
                return CensusProfileCharacteristic.POPULATION_DENSITY_PER_KM2
            elif 'median age' in value_lower:
                return CensusProfileCharacteristic.MEDIAN_AGE
            elif 'average age' in value_lower:
                return CensusProfileCharacteristic.AVERAGE_AGE
            elif 'total households' in value_lower or (value_lower.strip() == 'households' and 'total' in value_lower):
                return CensusProfileCharacteristic.TOTAL_HOUSEHOLDS
            elif 'average household size' in value_lower or 'household size' in value_lower:
                return CensusProfileCharacteristic.AVERAGE_HOUSEHOLD_SIZE
            elif 'total dwellings' in value_lower or (value_lower.strip() == 'dwellings' and 'total' in value_lower):
                return CensusProfileCharacteristic.TOTAL_DWELLINGS
            elif 'median household income' in value_lower or 'median total household income' in value_lower:
                return CensusProfileCharacteristic.MEDIAN_HOUSEHOLD_INCOME
            elif 'average household income' in value_lower or 'average total household income' in value_lower:
                return CensusProfileCharacteristic.AVERAGE_HOUSEHOLD_INCOME
        
        # Return None if no mapping found - keep original human-readable value
        return None
    
    @staticmethod
    def _create_dataframe(series_info: list[SeriesInfo]) -> pd.DataFrame:
        """
        Create the DataFrame from parsed series data with enhanced structure.
        
        Uses meaningful dimension names as column headers, with series key components
        available for reference and analysis.
        
        Args:
            series_info: List of SeriesInfo objects
            
        Returns:
            DataFrame with meaningful dimension columns plus time periods and values
        """
        rows = []
        
        for series in series_info:
            # Start with meaningful dimension names
            base_row = series.dimensions.copy()
            base_row['series_key'] = series.key
            
            # Add series key components as separate columns for advanced analysis
            key_components = series.key.split(':')
            for i, component in enumerate(key_components):
                base_row[f'dimension_{i}'] = component
            
            for time_period, value in series.observations.items():
                row: dict[str, str | float] = {}
                row.update(base_row)
                row['time_period'] = time_period
                row['value'] = value
                rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Reorder columns: meaningful dimensions first, then dimension components, then metadata
        meaningful_dims = [col for col in df.columns 
                          if col not in ['series_key', 'time_period', 'value'] 
                          and not col.startswith('dimension_')]
        dimension_components = [col for col in df.columns if col.startswith('dimension_')]
        metadata_cols = ['series_key', 'time_period', 'value']
        
        # Ensure all columns exist before reordering
        available_cols = []
        for col_group in [meaningful_dims, dimension_components, metadata_cols]:
            for col in col_group:
                if col in df.columns:
                    available_cols.append(col)
        
        return df[available_cols] if available_cols else df

    
    @classmethod
    def from_dataframe(cls, dataframe: pd.DataFrame) -> Self:
        """
        Create a CensusData instance from an existing DataFrame.
        
        This is useful when you have pre-processed data or want to create
        a CensusData instance from a subset of data. The DataFrame should
        contain columns for dimensions, series_key, time_period, and value.
        
        Args:
            dataframe: The DataFrame containing census data
            
        Returns:
            CensusData instance
        """
        return cls(dataframe)
    
    def filter_series(
        self, 
        gender: Optional[str] = None,
        characteristic: Optional[str] = None,
        statistic_type: Optional[str] = None
    ) -> list[SeriesInfo]:
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

    def filter_by_enhanced_filter(self, stats_filter: StatsFilter) -> list[SeriesInfo]:
        """
        Filter series using StatsFilter with enum values.
        
        Args:
            stats_filter: StatsFilter with enum-based filtering
            
        Returns:
            List of SeriesInfo matching the filter
        """
        filtered = []
        
        for series in self.series_info:
            matches = True
            
            # Check gender filter - now supports both enum values and string matching
            if stats_filter.gender:
                series_gender = series.dimensions.get('Gender', '')
                # Check if the stored value is already the enum
                if series_gender == stats_filter.gender:
                    pass  # Direct match
                else:
                    # Fallback to string matching for backward compatibility
                    gender_name = stats_filter.gender.name.replace('_', ' ').title()
                    if gender_name.lower() not in str(series_gender).lower():
                        matches = False
            
            # Check characteristic filter - now supports both enum values and string matching
            if stats_filter.census_profile_characteristic:
                series_char = series.dimensions.get('Characteristic', '') or series.dimensions.get('Census Profile Characteristic', '')
                # Check if the stored value is already the enum
                if series_char == stats_filter.census_profile_characteristic:
                    pass  # Direct match
                else:
                    # Fallback to string matching for backward compatibility
                    char_name = stats_filter.census_profile_characteristic.name.replace('_', ' ').title()
                    if char_name.lower() not in str(series_char).lower():
                        matches = False
            
            # Check statistic type filter - now supports both enum values and string matching
            if stats_filter.statistic_type:
                series_stat = series.dimensions.get('Statistic', '') or series.dimensions.get('Statistic Type', '')
                # Check if the stored value is already the enum
                if series_stat == stats_filter.statistic_type:
                    pass  # Direct match
                else:
                    # Fallback to string matching for backward compatibility
                    stat_name = stats_filter.statistic_type.name.replace('_', ' ').title()
                    if stat_name.lower() not in str(series_stat).lower():
                        matches = False
            
            if matches:
                filtered.append(series)
        
        return filtered

    def get_characteristics_by_category(self) -> dict[str, list[str]]:
        """
        Group available characteristics by category.
        
        Returns:
            Dict mapping category names to lists of characteristics
        """
        characteristics: dict[str, list[str]] = {}
        
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

    # DataFrame filtering and analysis methods
    def filter_by_gender(self, gender: str) -> pd.DataFrame:
        """Filter data by gender."""
        df = self.dataframe
        if 'Gender' in df.columns:
            return df[df['Gender'].str.contains(gender, case=False, na=False)]
        return df
    
    def filter_by_characteristic(self, characteristic: str) -> pd.DataFrame:
        """Filter data by census characteristic."""
        df = self.dataframe
        char_cols = [col for col in df.columns if 'characteristic' in col.lower()]
        if char_cols:
            col = char_cols[0]
            return df[df[col].str.contains(characteristic, case=False, na=False)]
        return df
    
    def get_population_data(self) -> pd.DataFrame:
        """Get only population-related data."""
        return self.filter_by_characteristic('population')
    
    def get_age_data(self) -> pd.DataFrame:
        """Get only age-related data.""" 
        return self.filter_by_characteristic('age')
    
    def get_household_data(self) -> pd.DataFrame:
        """Get only household-related data."""
        return self.filter_by_characteristic('household')
    
    def get_income_data(self) -> pd.DataFrame:
        """Get income-related data."""
        income_terms = ['income', 'earning', 'wage', 'salary']
        df = self.dataframe
        char_cols = [col for col in df.columns if 'characteristic' in col.lower()]
        if char_cols:
            mask = df[char_cols[0]].str.contains('|'.join(income_terms), case=False, na=False)
            return df[mask]
        return df

    def get_education_data(self) -> pd.DataFrame:
        """Get education-related data."""
        education_terms = ['education', 'school', 'degree', 'diploma', 'certificate']
        df = self.dataframe
        char_cols = [col for col in df.columns if 'characteristic' in col.lower()]
        if char_cols:
            mask = df[char_cols[0]].str.contains('|'.join(education_terms), case=False, na=False)
            return df[mask]
        return df

    def get_employment_data(self) -> pd.DataFrame:
        """Get employment-related data."""
        employment_terms = ['employment', 'labour', 'work', 'job', 'occupation']
        df = self.dataframe
        char_cols = [col for col in df.columns if 'characteristic' in col.lower()]
        if char_cols:
            mask = df[char_cols[0]].str.contains('|'.join(employment_terms), case=False, na=False)
            return df[mask]
        return df

    def get_dwelling_data(self) -> pd.DataFrame:
        """Get dwelling and housing-related data."""
        dwelling_terms = ['dwelling', 'housing', 'house', 'apartment', 'home']
        df = self.dataframe
        char_cols = [col for col in df.columns if 'characteristic' in col.lower()]
        if char_cols:
            mask = df[char_cols[0]].str.contains('|'.join(dwelling_terms), case=False, na=False)
            return df[mask]
        return df
    
    def pivot_by_gender(self) -> pd.DataFrame:
        """Pivot data to show gender breakdown by characteristic."""
        df = self.dataframe
        if 'Gender' in df.columns and 'value' in df.columns:
            char_col = next((col for col in df.columns if 'characteristic' in col.lower()), None)
            if char_col:
                return df.pivot_table(
                    index=char_col,
                    columns='Gender', 
                    values='value',
                    aggfunc='first'
                )
        return pd.DataFrame()
    
    def summary_stats(self) -> dict[str, Any]:
        """Get summary statistics for numeric columns."""
        df = self.dataframe
        numeric_cols = df.select_dtypes(include=['number']).columns
        return {
            'shape': df.shape,
            'numeric_columns': list(numeric_cols),
            'non_null_counts': df.count().to_dict(),
            'value_ranges': {col: {'min': df[col].min(), 'max': df[col].max()} 
                           for col in numeric_cols if col in df.columns}
        }

    def filter_by_enum(
        self, 
        gender: Optional[Gender] = None,
        characteristic: Optional[CensusProfileCharacteristic] = None,
        statistic_type: Optional[StatisticType] = None
    ) -> pd.DataFrame:
        """
        Filter data using enum values directly.
        
        Args:
            gender: Gender enum value to filter by
            characteristic: CensusProfileCharacteristic enum to filter by
            statistic_type: StatisticType enum to filter by
            
        Returns:
            Filtered DataFrame
        """
        df = self.dataframe
        
        if gender:
            if 'Gender' in df.columns:
                # Filter by enum value directly (more efficient) or fallback to name matching
                mask = (df['Gender'] == gender) | df['Gender'].astype(str).str.contains(
                    gender.name.replace('_', ' ').title(), case=False, na=False
                )
                df = df[mask]
        
        if characteristic:
            char_cols = [col for col in df.columns if 'characteristic' in col.lower()]
            if char_cols:
                col = char_cols[0]
                # Filter by enum value directly or fallback to name matching
                mask = (df[col] == characteristic) | df[col].astype(str).str.contains(
                    characteristic.name.replace('_', ' ').title(), case=False, na=False
                )
                df = df[mask]
        
        if statistic_type:
            stat_cols = [col for col in df.columns if 'statistic' in col.lower()]
            if stat_cols:
                col = stat_cols[0]
                # Filter by enum value directly or fallback to name matching
                mask = (df[col] == statistic_type) | df[col].astype(str).str.contains(
                    statistic_type.name.replace('_', ' ').title(), case=False, na=False
                )
                df = df[mask]
        
        return df

    def compare_by_gender(self) -> pd.DataFrame:
        """Create a comparison table by gender for key characteristics."""
        df = self.dataframe
        char_col = next((col for col in df.columns if 'characteristic' in col.lower()), None)
        gender_col = 'Gender' if 'Gender' in df.columns else None
        
        if char_col and gender_col and 'value' in df.columns:
            # Get latest values only
            latest = df.loc[df.groupby(['series_key'])['time_period'].idxmax()] if 'time_period' in df.columns else df
            
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

    def get_top_characteristics(self, n: int = 10, by_value: bool = True) -> pd.DataFrame:
        """
        Get the top N characteristics by value or other criteria.
        
        Args:
            n: Number of top characteristics to return
            by_value: Sort by value (True) or alphabetically (False)
            
        Returns:
            DataFrame with top characteristics
        """
        df = self.dataframe
        if 'value' not in df.columns:
            return df.head(n)
        
        # Get latest values
        latest = df.loc[df.groupby(['series_key'])['time_period'].idxmax()] if 'time_period' in df.columns else df
        
        if by_value:
            # Sort by value (handle NaN and non-numeric values)
            numeric_mask = pd.to_numeric(latest['value'], errors='coerce').notna()
            numeric_data = latest[numeric_mask].copy()
            numeric_data['value_numeric'] = pd.to_numeric(numeric_data['value'])
            top_data = numeric_data.nlargest(n, 'value_numeric')
        else:
            # Sort alphabetically by characteristic
            char_col = next((col for col in df.columns if 'characteristic' in col.lower()), None)
            if char_col:
                top_data = latest.sort_values(char_col).head(n)
            else:
                top_data = latest.head(n)
        
        return top_data

    

    def filter_by_stats_filter(self, stats_filter: StatsFilter) -> pd.DataFrame:
        """
        Filter DataFrame using a StatsFilter with efficient enum-based filtering.
        
        Args:
            stats_filter: StatsFilter with enum-based filtering
            
        Returns:
            Filtered DataFrame
        """
        return self.filter_by_enum(
            gender=stats_filter.gender,
            characteristic=stats_filter.census_profile_characteristic,
            statistic_type=stats_filter.statistic_type
        )

    
    def describe_structure(self) -> dict[str, Any]:
        """
        Get a comprehensive description of the data structure.
        
        Returns:
            Dictionary describing the dataset structure
        """
        df = self.dataframe
        
        return {
            'total_rows': len(df),
            'total_series': df['series_key'].nunique() if 'series_key' in df.columns else 0,
            'time_periods': sorted(df['time_period'].unique()) if 'time_period' in df.columns else [],
            'dimensions': {name: len(dim_info.values) for name, dim_info in self.dimensions.items()},
            'value_stats': {
                'non_null_values': df['value'].count() if 'value' in df.columns else 0,
                'numeric_values': pd.to_numeric(df['value'], errors='coerce').count() if 'value' in df.columns else 0,
                'value_range': {
                    'min': pd.to_numeric(df['value'], errors='coerce').min() if 'value' in df.columns else None,
                    'max': pd.to_numeric(df['value'], errors='coerce').max() if 'value' in df.columns else None
                } if 'value' in df.columns else None
            }
        }
    
    def get_population_summary(self) -> dict[str, Any]:
        """
        Get a summary of the population data including total, male, female, and ratio.
        
        Returns:
            Dictionary with population summary statistics
        """
        df = self.dataframe
        if 'Gender' not in df.columns or 'value' not in df.columns:
            return {}
        
        # Get latest data for accurate population counts
        latest_df = df.loc[df.groupby(['series_key'])['time_period'].idxmax()]
        
        # Filter for total, male, and female populations
        total_pop = latest_df[latest_df['Gender'].str.contains('Total', case=False, na=False)]
        male_pop = latest_df[latest_df['Gender'].str.contains('Male', case=False, na=False)]
        female_pop = latest_df[latest_df['Gender'].str.contains('Female', case=False, na=False)]
        
        # Calculate total population and male/female counts
        total_population = total_pop['value'].sum() if not total_pop.empty else 0
        male_population = male_pop['value'].sum() if not male_pop.empty else 0
        female_population = female_pop['value'].sum() if not female_pop.empty else 0
        
        # Calculate male to female ratio, avoid division by zero
        ratio = male_population / female_population if female_population > 0 else None
        
        return {
            'total_population': total_population,
            'male_population': male_population,
            'female_population': female_population,
            'male_female_ratio': ratio
        }

    def get_dimension_correlation(self) -> pd.DataFrame:
        """
        Calculate correlation between numeric dimensions in the data.
        
        Returns:
            DataFrame with correlation coefficients between dimensions
        """
        return self.dataframe.select_dtypes(include=['number']).corr()
    
    def get_cross_tabulation(self, row_dim: str, col_dim: str) -> pd.DataFrame:
        """
        Create a cross-tabulation between two dimensions.
        
        Args:
            row_dim: Dimension to use for rows
            col_dim: Dimension to use for columns
            
        Returns:
            Cross-tabulation DataFrame
        """
        return pd.crosstab(self.dataframe[row_dim], self.dataframe[col_dim], margins=True)
    
    def filter_by_gender_enum(self, gender: Gender) -> pd.DataFrame:
        """
        Filter data by Gender enum value.
        
        Args:
            gender: Gender enum value
            
        Returns:
            Filtered DataFrame
        """
        return self.filter_by_enum(gender=gender)
    
    def filter_by_characteristic_enum(self, characteristic: CensusProfileCharacteristic) -> pd.DataFrame:
        """
        Filter data by CensusProfileCharacteristic enum value.
        
        Args:
            characteristic: CensusProfileCharacteristic enum value
            
        Returns:
            Filtered DataFrame
        """
        return self.filter_by_enum(characteristic=characteristic)
    
    def filter_by_statistic_enum(self, statistic_type: StatisticType) -> pd.DataFrame:
        """
        Filter data by StatisticType enum value.
        
        Args:
            statistic_type: StatisticType enum value
            
        Returns:
            Filtered DataFrame
        """
        return self.filter_by_enum(statistic_type=statistic_type)
    
    def get_unique_enum_values(self) -> dict[str, list[Any]]:
        """
        Get unique enum values present in the DataFrame for each dimension.
        
        Returns:
            Dictionary mapping dimension names to lists of unique enum values
        """
        result: dict[str, list] = {}
        df = self.dataframe
        
        # Check Gender column for enum values
        if 'Gender' in df.columns:
            unique_genders = [val for val in df['Gender'].unique() if isinstance(val, Gender)]
            if unique_genders:
                result['Gender'] = unique_genders
        
        # Check Characteristic column for enum values
        char_cols = [col for col in df.columns if 'characteristic' in col.lower()]
        if char_cols:
            col = char_cols[0]
            unique_chars = [val for val in df[col].unique() if isinstance(val, CensusProfileCharacteristic)]
            if unique_chars:
                result['Characteristic'] = unique_chars
        
        # Check Statistic column for enum values
        stat_cols = [col for col in df.columns if 'statistic' in col.lower()]
        if stat_cols:
            col = stat_cols[0]
            unique_stats = [val for val in df[col].unique() if isinstance(val, StatisticType)]
            if unique_stats:
                result['Statistic'] = unique_stats
        
        return result
    
    def get_dimension_values_sample(self, limit: int = 10) -> dict[str, list[str]]:
        """
        Get a sample of unique dimension values for each column to help with mapping.
        
        Args:
            limit: Maximum number of unique values to return per dimension
            
        Returns:
            Dictionary mapping dimension names to lists of sample values
        """
        result = {}
        df = self.dataframe
        
        # Get meaningful dimension columns
        meaningful_dims = [col for col in df.columns 
                          if col not in ['series_key', 'time_period', 'value'] 
                          and not col.startswith('dimension_')]
        
        for col in meaningful_dims:
            unique_values = df[col].dropna().unique()
            # Convert to strings and take a sample
            sample_values = [str(val) for val in unique_values[:limit]]
            result[col] = sample_values
        
        return result
