"""Rent Burden indicator."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class RentBurdenCalculator(BaseCalculator):
    """
    Rent Burden: Rent CPI growth relative to wage growth.

    Measures whether rents are becoming more or less affordable
    relative to income growth.
    """

    INDICATOR_ID = "rent_burden"
    INDICATOR_NAME = "Rent Burden Index"
    CATEGORY = "household"
    DESCRIPTION = "Rent CPI year-over-year growth minus wage growth. Positive values indicate rents are rising faster than incomes, increasing housing burden."
    UNIT = "% differential"

    FRED_SERIES = [
        FredSeries(indicator_id="rent_burden", series_id="CUSR0000SEHA", role="rent_cpi"),  # Rent of primary residence
        FredSeries(indicator_id="rent_burden", series_id="CES0500000003", role="wages"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_max=0,        # Rents growing slower than wages is good
            yellow_max=2,       # Slightly faster is manageable
            red_min=2,          # Much faster is problematic
            invert=False        # Lower is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate rent growth minus wage growth."""
        df = df.ffill()

        rent_cpi = df["CUSR0000SEHA"]
        wages = df["CES0500000003"]

        # YoY percentage change
        rent_growth = rent_cpi.pct_change(periods=12) * 100
        wage_growth = wages.pct_change(periods=12) * 100

        # Rent burden: how much faster rents are growing vs wages
        burden = rent_growth - wage_growth

        return burden
