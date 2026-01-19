"""Yahoo Finance data collector."""
from typing import Optional
import pandas as pd
import yfinance as yf


def get_wilshire_5000(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.Series:
    """
    Fetch Wilshire 5000 index data from Yahoo Finance.

    The Wilshire 5000 Total Market Index represents the broadest index for the
    U.S. equity market. By historical design, the index value roughly equals
    total market cap in billions of dollars.

    Args:
        start_date: Start date in YYYY-MM-DD format (default: 1974-01-01)
        end_date: End date in YYYY-MM-DD format (default: today)

    Returns:
        pandas Series with date index and closing values
    """
    start = start_date or "1974-01-01"
    end = end_date or pd.Timestamp.today().strftime("%Y-%m-%d")

    ticker = yf.Ticker("^W5000")
    df = ticker.history(start=start, end=end)

    if df.empty:
        return pd.Series(dtype=float)

    # Return closing prices with date index
    series = df["Close"]
    series.index = pd.to_datetime(series.index.date)
    series.name = "W5000"

    return series
