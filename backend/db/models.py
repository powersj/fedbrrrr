"""Data models for FedBrrrr."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class Thresholds:
    """Threshold configuration for an indicator."""
    green_max: Optional[float] = None  # Values below this are green (good)
    green_min: Optional[float] = None  # Values above this are green (good)
    yellow_max: Optional[float] = None  # Values below this are yellow (caution)
    yellow_min: Optional[float] = None  # Values above this are yellow (caution)
    red_max: Optional[float] = None    # Values below this are red (bad)
    red_min: Optional[float] = None    # Values above this are red (bad)
    invert: bool = False  # If True, higher values are better

    def to_json(self) -> str:
        return json.dumps({
            "green_max": self.green_max,
            "green_min": self.green_min,
            "yellow_max": self.yellow_max,
            "yellow_min": self.yellow_min,
            "red_max": self.red_max,
            "red_min": self.red_min,
            "invert": self.invert,
        })

    @classmethod
    def from_json(cls, json_str: str) -> "Thresholds":
        data = json.loads(json_str)
        return cls(**data)


@dataclass
class Indicator:
    """An economic or household indicator."""
    id: str
    name: str
    category: str  # 'economy' or 'household'
    description: str = ""
    unit: str = ""
    thresholds: Thresholds = field(default_factory=Thresholds)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class FredSeries:
    """Mapping of FRED series to indicators."""
    indicator_id: str
    series_id: str
    role: str  # e.g., 'primary', 'numerator', 'denominator'


@dataclass
class DataPoint:
    """A single data point for an indicator."""
    indicator_id: str
    date: str  # ISO format YYYY-MM-DD
    value: float
    raw_values: dict = field(default_factory=dict)
    id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class UpdateLog:
    """Log entry for a data update operation."""
    indicator_id: str
    status: str  # 'success' or 'error'
    records_added: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    id: Optional[int] = None


def get_status_from_value(value: float, thresholds: Thresholds) -> str:
    """Determine the status (green/yellow/red) based on value and thresholds."""
    if thresholds.invert:
        # Higher values are better
        if thresholds.green_min is not None and value >= thresholds.green_min:
            return "green"
        if thresholds.yellow_min is not None and value >= thresholds.yellow_min:
            return "yellow"
        return "red"
    else:
        # Lower values are better (or specific ranges)
        if thresholds.green_max is not None and value <= thresholds.green_max:
            return "green"
        if thresholds.yellow_max is not None and value <= thresholds.yellow_max:
            return "yellow"
        if thresholds.red_min is not None and value >= thresholds.red_min:
            return "red"
        return "yellow"  # Default to yellow if no thresholds match
