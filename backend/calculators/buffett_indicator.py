"""Buffett Indicator - Market Cap to GDP ratio."""
from typing import Optional
import pandas as pd

from backend.db.models import FredSeries, Thresholds, DataPoint
from backend.collectors.yahoo_collector import get_wilshire_5000
from .base import BaseCalculator


class BuffettIndicatorCalculator(BaseCalculator):
    """
    Buffett Indicator: Total market cap to GDP ratio.

    Uses Wilshire 5000 Total Market Index from Yahoo Finance as the market cap proxy.
    The index value roughly equals total market cap in billions (by historical design).

    Values above 100% suggest overvaluation, above 150% extreme overvaluation.
    """

    INDICATOR_ID = "buffett_indicator"
    INDICATOR_NAME = "Buffett Indicator"
    CATEGORY = "economy"
    DESCRIPTION = "Total stock market capitalization to GDP ratio. Named after Warren Buffett who called it 'the best single measure of where valuations stand at any given moment.'"
    UNIT = "%"

    FRED_SERIES = [
        # GDP (quarterly, billions of dollars)
        FredSeries(indicator_id="buffett_indicator", series_id="GDP", role="gdp"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_max=100,      # Below 100% is reasonably valued
            yellow_max=150,     # 100-150% is elevated
            red_min=150,        # Above 150% is significantly overvalued
            invert=False        # Lower is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate market cap to GDP ratio as percentage."""
        df = df.ffill()

        # Wilshire 5000 index value ~= market cap in billions (by design)
        # GDP is also in billions
        ratio = (df["W5000"] / df["GDP"]) * 100

        return ratio

    def fetch_and_calculate(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[DataPoint]:
        """
        Fetch GDP from FRED and Wilshire 5000 from Yahoo Finance, then calculate.

        Args:
            start_date: Start date for data fetch
            end_date: End date for data fetch

        Returns:
            List of DataPoint objects with calculated values
        """
        # Fetch GDP from FRED
        gdp_series = self.collector.get_series("GDP", start_date, end_date)

        # Fetch Wilshire 5000 from Yahoo Finance
        wilshire_series = get_wilshire_5000(start_date, end_date)

        if gdp_series.empty or wilshire_series.empty:
            return []

        # Resample Wilshire 5000 daily data to quarterly
        # Use quarter-start (QS) to match FRED's GDP dating convention
        wilshire_quarterly = wilshire_series.resample("QS").last()

        # Combine into DataFrame
        df = pd.DataFrame({
            "GDP": gdp_series,
            "W5000": wilshire_quarterly
        })

        # Align dates - only keep rows where both values exist
        df = df.dropna()

        if df.empty:
            return []

        # Calculate indicator values
        values = self.calculate(df)
        values = values.dropna()

        # Convert to DataPoints
        data_points = []
        for date, value in values.items():
            raw_values = {
                "GDP": float(df.loc[date, "GDP"]),
                "W5000": float(df.loc[date, "W5000"])
            }

            data_points.append(DataPoint(
                indicator_id=self.INDICATOR_ID,
                date=date.strftime("%Y-%m-%d"),
                value=float(value),
                raw_values=raw_values
            ))

        return data_points
