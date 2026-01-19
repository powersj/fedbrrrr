"""Consumer Confidence (University of Michigan Sentiment)."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class ConsumerConfidenceCalculator(BaseCalculator):
    """
    University of Michigan Consumer Sentiment Index.

    Higher values indicate greater consumer confidence.
    Historically ranges from ~50 (pessimistic) to ~110 (optimistic).
    """

    INDICATOR_ID = "consumer_confidence"
    INDICATOR_NAME = "Consumer Confidence"
    CATEGORY = "economy"
    DESCRIPTION = "University of Michigan Consumer Sentiment Index. Measures consumer attitudes about the economy. Higher values indicate optimism, lower values indicate pessimism."
    UNIT = "Index"

    FRED_SERIES = [
        FredSeries(indicator_id="consumer_confidence", series_id="UMCSENT", role="primary"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_min=80,       # Above 80 is confident
            yellow_min=60,      # 60-80 is cautious
            red_max=60,         # Below 60 is pessimistic
            invert=True         # Higher is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Return consumer sentiment index directly."""
        return df["UMCSENT"]
