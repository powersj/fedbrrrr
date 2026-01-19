"""Base class for indicator calculators."""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

from backend.db.models import Indicator, DataPoint, FredSeries, Thresholds
from backend.db.repository import Repository
from backend.collectors.fred_collector import FredCollector


class BaseCalculator(ABC):
    """Abstract base class for indicator calculators."""

    # Subclasses must define these
    INDICATOR_ID: str = ""
    INDICATOR_NAME: str = ""
    CATEGORY: str = ""  # 'economy' or 'household'
    DESCRIPTION: str = ""
    UNIT: str = ""
    FRED_SERIES: list[FredSeries] = []  # Override in subclass

    def __init__(self, collector: FredCollector, repository: Repository):
        self.collector = collector
        self.repository = repository

    @abstractmethod
    def get_thresholds(self) -> Thresholds:
        """Return the thresholds for this indicator."""
        pass

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate the indicator values from raw FRED data.

        Args:
            df: DataFrame with FRED series data

        Returns:
            Series with calculated indicator values (date index)
        """
        pass

    def get_indicator(self) -> Indicator:
        """Get the Indicator model for this calculator."""
        return Indicator(
            id=self.INDICATOR_ID,
            name=self.INDICATOR_NAME,
            category=self.CATEGORY,
            description=self.DESCRIPTION,
            unit=self.UNIT,
            thresholds=self.get_thresholds()
        )

    def get_fred_series(self) -> list[FredSeries]:
        """Get the FRED series mappings for this calculator."""
        return [
            FredSeries(indicator_id=self.INDICATOR_ID, series_id=s.series_id, role=s.role)
            for s in self.FRED_SERIES
        ]

    def fetch_and_calculate(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> list[DataPoint]:
        """
        Fetch FRED data and calculate indicator values.

        Args:
            start_date: Start date for data fetch
            end_date: End date for data fetch

        Returns:
            List of DataPoint objects with calculated values
        """
        # Get series IDs needed
        series_ids = [s.series_id for s in self.FRED_SERIES]

        # Fetch data
        df = self.collector.get_multiple_series(series_ids, start_date, end_date)

        if df.empty:
            return []

        # Calculate indicator values
        values = self.calculate(df)
        values = values.dropna()

        # Convert to DataPoints
        data_points = []
        for date, value in values.items():
            raw_values = {}
            for series_id in series_ids:
                if series_id in df.columns and date in df.index:
                    raw_val = df.loc[date, series_id]
                    if pd.notna(raw_val):
                        raw_values[series_id] = float(raw_val)

            data_points.append(DataPoint(
                indicator_id=self.INDICATOR_ID,
                date=date.strftime("%Y-%m-%d"),
                value=float(value),
                raw_values=raw_values
            ))

        return data_points

    def update(self, full_refresh: bool = False) -> int:
        """
        Update the indicator data in the database.

        Args:
            full_refresh: If True, fetch all historical data. If False, fetch only new data.

        Returns:
            Number of data points added/updated
        """
        # Seed indicator metadata
        self.repository.upsert_indicator(self.get_indicator())

        # Add FRED series mappings
        for series in self.get_fred_series():
            self.repository.add_fred_series(series)

        # Determine start date
        start_date = None
        if not full_refresh:
            latest_date = self.repository.get_latest_date(self.INDICATOR_ID)
            if latest_date:
                start_date = latest_date

        # Log update start
        log_id = self.repository.log_update_start(self.INDICATOR_ID)

        try:
            # Fetch and calculate
            data_points = self.fetch_and_calculate(start_date=start_date)

            # Store results
            count = self.repository.upsert_data_points(data_points)

            # Log success
            self.repository.log_update_complete(log_id, count)

            return count

        except Exception as e:
            self.repository.log_update_error(log_id, str(e))
            raise
