"""Personal Savings Rate indicator."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class PersonalSavingsCalculator(BaseCalculator):
    """
    Personal Savings Rate.

    Percentage of disposable income that households save.
    Low rates suggest households are stretched or overspending.
    """

    INDICATOR_ID = "personal_savings"
    INDICATOR_NAME = "Personal Savings Rate"
    CATEGORY = "household"
    DESCRIPTION = "Personal saving as a percentage of disposable personal income. Low rates indicate households have limited financial cushion; high rates may indicate economic uncertainty."
    UNIT = "%"

    FRED_SERIES = [
        FredSeries(indicator_id="personal_savings", series_id="PSAVERT", role="primary"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_min=6,        # Above 6% is healthy
            yellow_min=3,       # 3-6% is low but manageable
            red_max=3,          # Below 3% is concerning
            invert=True         # Higher is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Return personal savings rate directly."""
        return df["PSAVERT"]
