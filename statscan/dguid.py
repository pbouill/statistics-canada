"""Data Geographic Unique Identifier (DGUID) functionality for StatsCan datasets."""

import logging
from dataclasses import dataclass

import pandas as pd

from statscan.enums.frequency import Frequency
from statscan.enums.geocode.geocode import GeoCode
from statscan.enums.schema import Schema
from statscan.enums.stats_filter import StatsFilter
from statscan.enums.vintage import Vintage
from statscan.enums.wds.wds import Detail, Format
from statscan.sdmx.response import SDMXResponse
from statscan.util.get_data import get_sdmx_data, make_census_profile_key

logger = logging.getLogger(__name__)


@dataclass
class DGUID:
    """Data Geographic Unique Identifier (DGUID) for StatsCan datasets.

    See: https://www12.statcan.gc.ca/wds-sdw/2021profile-profil2021-eng.cfm.

    """

    geocode: GeoCode
    vintage: Vintage = Vintage.CENSUS_2021  # Default vintage is Census 2021
    _sdmx_response: SDMXResponse | None = None  # Cached data response, if available
    DEFAULT_TIMEOUT: int = 60  # seconds

    @property
    def schema(self) -> Schema:
        """Get the schema for the DGUID.

        Returns
        -------
        Schema
            The schema associated with the DGUID.

        """
        return self.geocode.schema

    @property
    def data_flow(self) -> str:
        """Get the data flow for the DGUID.

        Returns
        -------
        str
            The data flow associated with the DGUID.

        """
        return self.schema.data_flow

    def key(
        self,
        frequency: Frequency = Frequency.A5,
        stats_filter: StatsFilter | None = None,
    ) -> str:
        """Generate a 5-dimension SDMX key for this DGUID.

        Returns:
            str: A 5-dimension key compatible with Census Profile SDMX API.

        """
        return make_census_profile_key(
            dguid=str(self), frequency=frequency, stats_filter=stats_filter
        )

    def __str__(self) -> str:
        """Return string representation of DGUID."""
        return f"{self.vintage.value}{self.geocode.code}"

    async def _get_sdmx_response(
        self,
        frequency: Frequency = Frequency.A5,
        stats_filter: StatsFilter | None = None,
        detail: Detail | None = None,
        timeout: float | None = None,
    ) -> SDMXResponse:
        """Get data for the DGUID from the WDS API.

        Args:
            self (DGUID): The DGUID instance.
            frequency (Frequency, optional): The frequency of the data.
            stats_filter (StatsFilter, optional): The statistical filter to apply.
            detail: Detail level for the response
            timeout: Request timeout in seconds

        Returns:
            Response: The API response containing the data.

        """
        resp = await get_sdmx_data(
            flow_ref=self.data_flow,
            dguid=f"{self}",
            frequency=frequency,
            stats_filter=stats_filter,
            format=Format.JSONDATA,
            detail=detail,
            timeout=timeout,
        )
        raw_data = resp.json()
        sdmx_response = SDMXResponse.model_validate(obj=raw_data)
        sdmx_response._raw_data = raw_data  # Store raw data for DataFrame conversion
        return sdmx_response

    async def update(
        self,
        frequency: Frequency = Frequency.A5,
        stats_filter: StatsFilter | None = None,
        detail: Detail | None = None,
        timeout: float | None = None,
        # raise_on_error: bool = False,
    ) -> None:
        """Update the cached SDMX response.

        Swallows exceptions by default (tests can proceed) but logs them.
        Set raise_on_error=True to propagate exceptions for debugging.

        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        self._sdmx_response = await self._get_sdmx_response(
            frequency=frequency,
            stats_filter=stats_filter,
            detail=detail,
            timeout=timeout,
        )
        logger.debug(
            "Updated SDMX response for %s (flow=%s, freq=%s)",
            self,
            self.data_flow,
            frequency,
        )

    @property
    def sdmx_response(self) -> SDMXResponse | None:
        """Get the cached SDMX response for this DGUID."""
        return self._sdmx_response

    @property
    def dataframe(self) -> pd.DataFrame | None:
        """Get the cached SDMX response data as a DataFrame.

        Returns
        -------
        pd.DataFrame
            The cached DataFrame, or None if not available.

        """
        if self.sdmx_response is None:
            return None
        return self.sdmx_response.dataframe

    @property
    def population_data(self) -> pd.DataFrame | None:
        """Return cached population-related rows (None if not yet updated)."""
        if self.sdmx_response is None:
            return None
        try:
            df = self.sdmx_response.get_population_data()
            if df is None or df.empty:
                return df
            needed = {"Gender", "Characteristic", "Value"}
            if not needed.issubset(df.columns):
                return df
            return df
        except Exception:
            return None

    # Convenience: ensure updated
    async def ensure_updated(
        self, timeout: float | None = None, **update_kwargs
    ) -> None:
        """Ensure data is loaded.

        Pass extra kwargs to update() (e.g., raise_on_error=True).

        """
        if self.sdmx_response is None:
            await self.update(timeout=timeout, **update_kwargs)

    # Generic characteristic lookup helpers
    def _characteristic_selector(
        self, characteristic_substr: str, gender: str | None = None
    ) -> pd.Series | None:
        if self.dataframe is None:
            return None
        df = self.dataframe
        if "Characteristic" not in df.columns:
            return None
        mask = (
            df["Characteristic"]
            .astype(str)
            .str.contains(characteristic_substr, case=False, na=False)
        )
        if gender and "Gender" in df.columns:
            mask &= df["Gender"] == gender
        subset = df[mask]
        if subset.empty:
            return None
        # Prefer a non-null Value
        if "Value" in subset.columns:
            non_null = subset[subset["Value"].notna()]
            if not non_null.empty:
                return non_null.iloc[0]
        return subset.iloc[0]

    def get_characteristic_value(
        self, characteristic_substr: str, gender: str | None = "Total - Gender"
    ) -> float | None:
        """Get numeric value for a characteristic, optionally filtered by gender."""
        row = self._characteristic_selector(characteristic_substr, gender)
        if row is None:
            return None
        val = row.get("Value")
        try:
            return float(val)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    # Specific convenience properties
    @property
    def total_population_2021(self) -> int | None:
        """Get total population from 2021 census."""
        val = self.get_characteristic_value("Population, 2021")
        return int(val) if val is not None else None

    @property
    def population_change_2016_2021(self) -> float | None:
        """Get population percentage change from 2016 to 2021."""
        return self.get_characteristic_value(
            "Population percentage change, 2016 to 2021"
        )

    @property
    def land_area_km2(self) -> float | None:
        """Get land area in square kilometres."""
        return self.get_characteristic_value("Land area in square kilometres")

    @property
    def population_density(self) -> float | None:
        """Get population density per square kilometre."""
        return self.get_characteristic_value("Population density per square kilometre")

    # --- Demographic slice helpers ---
    def _slice_by_terms(
        self, terms: list[str], must_have: list[str] | None = None
    ) -> pd.DataFrame | None:
        if self.dataframe is None:
            return None
        df = self.dataframe
        if "Characteristic" not in df.columns:
            return None
        mask = pd.Series(False, index=df.index)
        lower_char = df["Characteristic"].astype(str).str.lower()
        for t in terms:
            mask |= lower_char.str.contains(t, na=False)
        if must_have:
            for t in must_have:
                mask &= lower_char.str.contains(t, na=False)
        subset = df[mask]
        return subset if not subset.empty else None

    @property
    def gender_demographics(self) -> pd.DataFrame | None:
        """Get rows involving gender breakdown.

        Excludes total-only rows unless no breakdown.

        """
        if self.dataframe is None:
            return None
        df = self.dataframe
        if "Gender" not in df.columns:
            return None
        if "Characteristic" not in df.columns:
            return None
        # pick characteristics where we have multiple genders
        grouped = df.groupby(["Characteristic"]).filter(
            lambda g: g["Gender"].nunique() > 1
        )
        return grouped if not grouped.empty else None

    @property
    def age_demographics_df(self) -> pd.DataFrame | None:
        """Age-related demographic DataFrame (standardized)."""
        return self._slice_by_terms(["age"])

    @property
    def income_statistics(self) -> pd.DataFrame | None:
        """Income related statistics subset (includes groups, median, average, etc.)."""
        return self._slice_by_terms(["income"])

    def get_income_stat(
        self, stat_substr: str, gender: str | None = "Total - Gender"
    ) -> float | None:
        """Get income statistic value.

        Filtered by characteristic substring and gender.

        """
        return self.get_characteristic_value(stat_substr, gender)

    async def get_dataframe(self, timeout: float | None = None) -> pd.DataFrame:
        """Get data as a DataFrame, updating if needed.

        Args:
            timeout: Request timeout in seconds

        Returns:
            DataFrame with the data

        """
        if self.sdmx_response is None:
            await self.update(timeout=timeout)
        if self.sdmx_response is None:
            return pd.DataFrame()
        return self.sdmx_response.dataframe

    async def get_response(
        self, timeout: float | None = None
    ) -> SDMXResponse | None:
        """Get the SDMX response, updating if needed.

        Args:
            timeout: Request timeout in seconds

        Returns:
            The SDMX response

        """
        if self.sdmx_response is None:
            await self.update(timeout=timeout)
        return self.sdmx_response

    async def get_population_data(
        self, timeout: float | None = None
    ) -> pd.DataFrame:
        """Async retrieval of population data (empty DataFrame if unavailable)."""
        if self.sdmx_response is None:
            await self.update(timeout=timeout)
        if self.sdmx_response is None:
            return pd.DataFrame()
        try:
            df = self.sdmx_response.get_population_data()
            return df if df is not None else pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    async def get_age_demographics(
        self, timeout: float | None = None
    ) -> pd.DataFrame:
        """Get age demographic data, updating if needed.

        Args:
            timeout: Request timeout in seconds

        Returns:
            DataFrame with age demographic data

        """
        if self.sdmx_response is None:
            await self.update(timeout=timeout)
        if self.sdmx_response is None:
            return pd.DataFrame()
        return self.sdmx_response.get_age_demographics()

    async def get_gender_demographics(
        self, timeout: float | None = None
    ) -> pd.DataFrame:
        """Get gender demographic data, updating if needed.

        Args:
            timeout: Request timeout in seconds

        Returns:
            DataFrame with gender demographic data

        """
        await self.ensure_updated(timeout=timeout)
        return (
            self.gender_demographics
            if self.gender_demographics is not None
            else pd.DataFrame()
        )

    async def get_income_statistics(
        self, timeout: float | None = None
    ) -> pd.DataFrame:
        """Get income statistics, updating if needed.

        Args:
            timeout: Request timeout in seconds

        Returns:
            DataFrame with income statistics

        """
        await self.ensure_updated(timeout=timeout)
        return (
            self.income_statistics
            if self.income_statistics is not None
            else pd.DataFrame()
        )

    @property
    def url(self) -> str:
        """Get the URL for accessing this DGUID's data.

        Returns:
            The SDMX API URL for this DGUID

        """
        # This is a placeholder implementation - adjust based on actual API structure
        return f"https://www150.statcan.gc.ca/t1/wds/rest/getDataFromTable/sdmx/{self.data_flow}/{self}"
