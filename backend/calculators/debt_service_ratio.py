"""Household Debt Service Ratio indicator."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class DebtServiceRatioCalculator(BaseCalculator):
    """
    Household Debt Service Ratio.

    Total household debt payments as percentage of disposable income.
    Higher ratios indicate households are more leveraged.
    """

    INDICATOR_ID = "debt_service_ratio"
    INDICATOR_NAME = "Debt Service Ratio"
    CATEGORY = "household"
    DESCRIPTION = "Total household debt payments (mortgage, consumer debt) as percentage of disposable personal income. Higher values indicate more household financial stress."
    UNIT = "%"

    FRED_SERIES = [
        FredSeries(indicator_id="debt_service_ratio", series_id="TDSP", role="primary"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_max=10,       # Below 10% is comfortable
            yellow_max=12,      # 10-12% is manageable
            red_min=12,         # Above 12% is stressed
            invert=False        # Lower is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Return debt service ratio directly."""
        return df["TDSP"]
