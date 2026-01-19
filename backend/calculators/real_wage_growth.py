"""Real Wage Growth indicator."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class RealWageGrowthCalculator(BaseCalculator):
    """
    Real Wage Growth: Nominal wage growth minus inflation.

    Positive values mean wages are outpacing inflation.
    Negative values mean purchasing power is declining.
    """

    INDICATOR_ID = "real_wage_growth"
    INDICATOR_NAME = "Real Wage Growth"
    CATEGORY = "household"
    DESCRIPTION = "Year-over-year growth in average hourly earnings minus CPI inflation. Positive values indicate rising purchasing power, negative values indicate declining living standards."
    UNIT = "% YoY"

    FRED_SERIES = [
        FredSeries(indicator_id="real_wage_growth", series_id="CES0500000003", role="wages"),  # Avg hourly earnings
        FredSeries(indicator_id="real_wage_growth", series_id="CPIAUCSL", role="cpi"),  # CPI
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_min=1.0,      # Above 1% real growth is healthy
            yellow_min=0,       # Flat is concerning
            red_max=0,          # Negative means declining purchasing power
            invert=True         # Higher is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate real wage growth (nominal wages - inflation)."""
        df = df.ffill()

        wages = df["CES0500000003"]
        cpi = df["CPIAUCSL"]

        # YoY percentage change (12 months)
        wage_growth = wages.pct_change(periods=12) * 100
        inflation = cpi.pct_change(periods=12) * 100

        # Real wage growth
        real_growth = wage_growth - inflation

        return real_growth
