"""Mortgage Affordability indicator."""
import pandas as pd
import numpy as np

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class MortgageAffordabilityCalculator(BaseCalculator):
    """
    Mortgage Affordability: Monthly payment as % of median household income.

    Calculates what percentage of median income is needed for a mortgage
    on a median-priced home at current rates.
    """

    INDICATOR_ID = "mortgage_affordability"
    INDICATOR_NAME = "Mortgage Affordability"
    CATEGORY = "household"
    DESCRIPTION = "Estimated mortgage payment for median home as percentage of median household income. Based on 30-year mortgage rates, median home price, and 20% down payment."
    UNIT = "% of income"

    FRED_SERIES = [
        FredSeries(indicator_id="mortgage_affordability", series_id="MORTGAGE30US", role="mortgage_rate"),
        FredSeries(indicator_id="mortgage_affordability", series_id="MSPUS", role="median_home_price"),
        FredSeries(indicator_id="mortgage_affordability", series_id="MEHOINUSA672N", role="median_income"),
    ]

    def get_thresholds(self) -> Thresholds:
        return Thresholds(
            green_max=25,       # Below 25% of income is affordable
            yellow_max=35,      # 25-35% is stretched
            red_min=35,         # Above 35% is unaffordable
            invert=False        # Lower is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """Calculate mortgage payment as % of monthly income."""
        # Forward fill to align different frequencies
        df = df.ffill()

        rate = df["MORTGAGE30US"] / 100 / 12  # Monthly rate
        home_price = df["MSPUS"]
        annual_income = df["MEHOINUSA672N"]

        # Loan amount (80% of home price with 20% down)
        loan_amount = home_price * 0.80

        # Monthly payment calculation (standard mortgage formula)
        # M = P * [r(1+r)^n] / [(1+r)^n - 1]
        n = 360  # 30 years * 12 months
        monthly_payment = loan_amount * (rate * (1 + rate)**n) / ((1 + rate)**n - 1)

        # Handle edge case where rate is 0
        monthly_payment = monthly_payment.replace([np.inf, -np.inf], np.nan)

        # Monthly income
        monthly_income = annual_income / 12

        # Payment as percentage of income
        affordability = (monthly_payment / monthly_income) * 100

        return affordability
