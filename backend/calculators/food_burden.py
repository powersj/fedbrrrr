"""Food Burden indicator."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class FoodBurdenCalculator(BaseCalculator):
    """
    Food Burden: Food CPI growth relative to wage growth.

    Measures whether food costs are becoming more or less affordable
    relative to income growth.
    """

    INDICATOR_ID = "food_burden"
    INDICATOR_NAME = "Food Burden Index"
    CATEGORY = "household"
    DESCRIPTION = "Food CPI year-over-year growth minus wage growth. Positive values indicate food costs are rising faster than incomes, squeezing household budgets."
    UNIT = "% differential"

    FRED_SERIES = [
        FredSeries(indicator_id="food_burden", series_id="CPIUFDNS", role="food_cpi"),  # Food CPI
        FredSeries(indicator_id="food_burden", series_id="CES0500000003", role="wages"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_max=0,        # Food growing slower than wages is good
            yellow_max=2,       # Slightly faster is manageable
            red_min=2,          # Much faster is problematic
            invert=False        # Lower is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate food CPI growth minus wage growth."""
        df = df.ffill()

        food_cpi = df["CPIUFDNS"]
        wages = df["CES0500000003"]

        # YoY percentage change
        food_growth = food_cpi.pct_change(periods=12) * 100
        wage_growth = wages.pct_change(periods=12) * 100

        # Food burden: how much faster food costs are growing vs wages
        burden = food_growth - wage_growth

        return burden
