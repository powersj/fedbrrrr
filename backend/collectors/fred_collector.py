"""FRED API data collector."""
import time
from datetime import datetime
from typing import Optional
import pandas as pd
from fredapi import Fred

from backend.config import FRED_API_KEY


class FredCollector:
    """Collector for FRED economic data."""

    # Rate limiting: FRED allows 120 requests per minute
    REQUEST_DELAY = 0.5  # seconds between requests

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or FRED_API_KEY
        if not self.api_key:
            raise ValueError("FRED API key is required")
        self.fred = Fred(api_key=self.api_key)
        self._last_request_time = 0.0

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self._last_request_time = time.time()

    def get_series(
        self,
        series_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.Series:
        """
        Fetch a FRED series.

        Args:
            series_id: FRED series identifier (e.g., 'GDP', 'UNRATE')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            pandas Series with date index and values
        """
        self._rate_limit()

        kwargs = {}
        if start_date:
            kwargs["observation_start"] = start_date
        if end_date:
            kwargs["observation_end"] = end_date

        series = self.fred.get_series(series_id, **kwargs)
        return series

    def get_series_info(self, series_id: str) -> dict:
        """Get metadata about a FRED series."""
        self._rate_limit()
        info = self.fred.get_series_info(series_id)
        return info.to_dict()

    def get_multiple_series(
        self,
        series_ids: list[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        align_dates: bool = True
    ) -> pd.DataFrame:
        """
        Fetch multiple FRED series and combine them.

        Args:
            series_ids: List of FRED series identifiers
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            align_dates: If True, forward-fill to align different frequencies

        Returns:
            DataFrame with date index and columns for each series
        """
        data = {}
        for series_id in series_ids:
            try:
                series = self.get_series(series_id, start_date, end_date)
                data[series_id] = series
            except Exception as e:
                print(f"Error fetching {series_id}: {e}")
                continue

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        if align_dates:
            # Forward-fill to handle different frequencies
            df = df.ffill()

        return df

    def get_latest_value(self, series_id: str) -> tuple[str, float]:
        """
        Get the most recent value for a series.

        Returns:
            Tuple of (date string, value)
        """
        series = self.get_series(series_id)
        series = series.dropna()
        if series.empty:
            raise ValueError(f"No data available for series {series_id}")

        latest_date = series.index[-1]
        latest_value = series.iloc[-1]

        return latest_date.strftime("%Y-%m-%d"), float(latest_value)


# Singleton instance for reuse
_collector: Optional[FredCollector] = None


def get_collector() -> FredCollector:
    """Get or create the FRED collector singleton."""
    global _collector
    if _collector is None:
        _collector = FredCollector()
    return _collector
