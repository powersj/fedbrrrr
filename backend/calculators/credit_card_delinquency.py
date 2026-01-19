"""Credit Card Delinquency Rate indicator."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class CreditCardDelinquencyCalculator(BaseCalculator):
    """
    Credit Card Delinquency Rate.

    Percentage of credit card balances 90+ days delinquent.
    Rising rates indicate household financial stress.
    """

    INDICATOR_ID = "credit_card_delinquency"
    INDICATOR_NAME = "Credit Card Delinquency"
    CATEGORY = "household"
    DESCRIPTION = "Percentage of credit card balances that are 90+ days past due. Rising delinquencies signal household financial stress and potential consumer spending slowdown."
    UNIT = "%"

    FRED_SERIES = [
        FredSeries(indicator_id="credit_card_delinquency", series_id="DRCCLACBS", role="primary"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_max=2.5,      # Below 2.5% is healthy
            yellow_max=4.0,     # 2.5-4% is elevated
            red_min=4.0,        # Above 4% is concerning
            invert=False        # Lower is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Return credit card delinquency rate directly."""
        return df["DRCCLACBS"]
