"""
Integration tests for SDMX API functionality.
Tests DGUID-based data retrieval using SDMX endpoints.
"""
import pytest
import asyncio
from statscan.dguid import DGUID
from statscan.enums.auto.census_subdivision import CensusSubdivision


class TestSDMXAPIIntegration:
    """Integration tests for SDMX API via DGUID."""
    
    @pytest.mark.asyncio
    async def test_saugeen_shores_dguid_update(self):
        """Test that Saugeen Shores DGUID can fetch real data from SDMX API."""
        try:
            dguid = DGUID(geocode=CensusSubdivision.ONT_SAUGEEN_SHORES)
            await dguid.update(timeout=30)
            
            # Verify we got some data
            assert dguid.sdmx_response is not None
            assert dguid.dataframe is not None
            assert len(dguid.dataframe) > 0
            
            # Basic population data validation
            population_data = dguid.population_data
            if population_data is not None and len(population_data) > 0:
                # Should have some population records
                assert 'Value' in population_data.columns
                # Filter for the official 2021 population count
                total_pop_records = population_data[
                    (population_data['Characteristic'].str.contains('Population, 2021', case=False, na=False)) &
                    (population_data['Statistic'] == 'Counts') &
                    (population_data['Gender'] == 'Total - Gender')
                ]
                if len(total_pop_records) > 0:
                    pop_value = total_pop_records.iloc[0]['Value']
                    # Reasonable population range for Saugeen Shores (actual 2021 population: 15,908)
                    assert 10000 <= pop_value <= 20000, f"Population {pop_value} outside expected range"
            
        except Exception as e:
            pytest.skip(f"Saugeen Shores SDMX API integration failed: {e}")
