"""M2 Money Supply growth indicator."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class M2GrowthCalculator(BaseCalculator):
    """
    M2 Money Supply year-over-year growth.

    High growth can signal future inflation.
    Negative growth is historically rare and concerning.
    """

    INDICATOR_ID = "m2_growth"
    INDICATOR_NAME = "M2 Money Supply Growth"
    CATEGORY = "economy"
    DESCRIPTION = "Year-over-year change in M2 money supply. High growth often precedes inflation; negative growth is historically rare and can signal deflationary pressure."
    UNIT = "% YoY"

    FRED_SERIES = [
        FredSeries(indicator_id="m2_growth", series_id="M2SL", role="primary"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_max=8,        # Healthy 3-8% growth
            green_min=3,
            yellow_max=12,      # Elevated
            yellow_min=0,       # Flat to slightly positive
            red_min=12,         # Inflationary
            invert=False
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate year-over-year percentage change in M2."""
        m2 = df["M2SL"]

        # YoY percentage change (12 months for monthly data)
        yoy_change = m2.pct_change(periods=12) * 100

        return yoy_change
