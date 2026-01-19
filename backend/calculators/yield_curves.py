"""Yield Curve indicators - 10Y-2Y and 10Y-3M spreads."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class YieldCurve10Y2YCalculator(BaseCalculator):
    """
    10-Year minus 2-Year Treasury yield spread.

    Negative values (inversion) historically precede recessions.
    """

    INDICATOR_ID = "yield_curve_10y2y"
    INDICATOR_NAME = "Yield Curve (10Y-2Y)"
    CATEGORY = "economy"
    DESCRIPTION = "Spread between 10-year and 2-year Treasury yields. Inversion (negative values) has preceded every US recession since 1970."
    UNIT = "%"

    FRED_SERIES = [
        FredSeries(indicator_id="yield_curve_10y2y", series_id="DGS10", role="long_rate"),
        FredSeries(indicator_id="yield_curve_10y2y", series_id="DGS2", role="short_rate"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_min=0.5,      # Healthy spread above 0.5%
            yellow_min=0,       # Flat to slightly positive
            red_max=0,          # Inverted (negative) is warning
            invert=True         # Higher spread is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate 10Y-2Y spread."""
        spread = df["DGS10"] - df["DGS2"]
        return spread


class YieldCurve10Y3MCalculator(BaseCalculator):
    """
    10-Year minus 3-Month Treasury yield spread.

    More sensitive to near-term recession risk than 10Y-2Y.
    """

    INDICATOR_ID = "yield_curve_10y3m"
    INDICATOR_NAME = "Yield Curve (10Y-3M)"
    CATEGORY = "economy"
    DESCRIPTION = "Spread between 10-year and 3-month Treasury yields. Often considered a more reliable recession indicator than the 10Y-2Y spread."
    UNIT = "%"

    FRED_SERIES = [
        FredSeries(indicator_id="yield_curve_10y3m", series_id="DGS10", role="long_rate"),
        FredSeries(indicator_id="yield_curve_10y3m", series_id="DGS3MO", role="short_rate"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_min=1.0,      # Healthy spread above 1%
            yellow_min=0,       # Flat to positive
            red_max=0,          # Inverted is warning
            invert=True         # Higher spread is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate 10Y-3M spread."""
        spread = df["DGS10"] - df["DGS3MO"]
        return spread
