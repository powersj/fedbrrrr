"""Sahm Rule recession indicator."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class SahmRuleCalculator(BaseCalculator):
    """
    Sahm Rule: 3-month moving average of unemployment rate vs 12-month low.

    When the 3-month MA rises 0.5% above its 12-month low, a recession
    has historically begun or is imminent.
    """

    INDICATOR_ID = "sahm_rule"
    INDICATOR_NAME = "Sahm Rule"
    CATEGORY = "economy"
    DESCRIPTION = "Compares the 3-month moving average of unemployment to its 12-month low. A rise of 0.5% or more signals recession onset. Created by economist Claudia Sahm."
    UNIT = "%"

    FRED_SERIES = [
        FredSeries(indicator_id="sahm_rule", series_id="UNRATE", role="primary"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_max=0.3,      # Below 0.3% is safe
            yellow_max=0.5,     # 0.3-0.5% is caution
            red_min=0.5,        # 0.5%+ signals recession
            invert=False        # Lower is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Sahm Rule indicator."""
        unrate = df["UNRATE"]

        # 3-month moving average
        ma_3m = unrate.rolling(window=3, min_periods=3).mean()

        # 12-month rolling minimum
        min_12m = unrate.rolling(window=12, min_periods=12).min()

        # Sahm indicator: difference between 3-month MA and 12-month low
        sahm = ma_3m - min_12m

        return sahm
