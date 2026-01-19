"""Fed Balance Sheet indicator - Total assets YoY growth."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class FedBalanceSheetCalculator(BaseCalculator):
    """
    Federal Reserve Balance Sheet year-over-year growth.

    Rapid expansion indicates aggressive monetary stimulus.
    Contraction (negative growth) indicates quantitative tightening.
    """

    INDICATOR_ID = "fed_balance_sheet"
    INDICATOR_NAME = "Fed Balance Sheet"
    CATEGORY = "economy"
    DESCRIPTION = "Year-over-year change in Federal Reserve total assets. Expansion indicates monetary stimulus (QE), contraction indicates tightening (QT)."
    UNIT = "% YoY"

    FRED_SERIES = [
        FredSeries(indicator_id="fed_balance_sheet", series_id="WALCL", role="primary"),
    ]

    def get_thresholds(self) -> Thresholds:
        # This is more nuanced - both extremes can be concerning
        # High growth = emergency stimulus mode
        # Negative growth = tightening, can stress markets
        return Thresholds(
            green_max=10,       # Moderate growth/stable
            green_min=-5,       # Slight contraction OK
            yellow_max=25,      # Elevated expansion
            yellow_min=-10,     # Moderate contraction
            red_min=25,         # Emergency stimulus level
            invert=False
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate year-over-year percentage change in Fed assets."""
        assets = df["WALCL"]

        # YoY percentage change (52 weeks for weekly data)
        yoy_change = assets.pct_change(periods=52) * 100

        return yoy_change
