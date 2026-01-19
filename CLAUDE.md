# Claude Development Guide

## Adding a New Indicator

### 1. Create the Calculator

Create a new file in `backend/calculators/` (e.g., `my_indicator.py`):

```python
"""My Indicator description."""
import pandas as pd

from backend.db.models import FredSeries, Thresholds
from .base import BaseCalculator


class MyIndicatorCalculator(BaseCalculator):
    """
    Docstring explaining the indicator.
    """

    INDICATOR_ID = "my_indicator"           # Unique ID (used in URLs/filenames)
    INDICATOR_NAME = "My Indicator"         # Display name
    CATEGORY = "economy"                    # "economy" or "household"
    DESCRIPTION = "What this indicator measures and why it matters."
    UNIT = "%"                              # Unit for display (%, $, index, etc.)

    FRED_SERIES = [
        # List all FRED series needed for calculation
        FredSeries(indicator_id="my_indicator", series_id="SERIES_ID", role="primary"),
        # Add more if indicator combines multiple series
    ]

    def get_thresholds(self) -> Thresholds:
        """Define green/yellow/red thresholds."""
        return Thresholds(
            green_max=50,       # Green if value <= 50
            yellow_max=75,      # Yellow if 50 < value <= 75
            red_min=75,         # Red if value > 75
            invert=False        # False = lower is better, True = higher is better
        )

    def calculate(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate indicator from FRED data.

        Args:
            df: DataFrame with columns matching FRED_SERIES series_ids

        Returns:
            Series with calculated values (date index)
        """
        # Access FRED series by their series_id
        series = df["SERIES_ID"]

        # Perform calculation
        result = series  # or some transformation

        return result
```

### 2. Register the Calculator

Edit `backend/calculators/__init__.py`:

```python
from .my_indicator import MyIndicatorCalculator

ALL_CALCULATORS = [
    # ... existing calculators ...
    MyIndicatorCalculator,  # Add to economy or household section
]
```

### 3. Run Full Refresh

```bash
uv run python -m backend.main --full-refresh
```

This will:
1. Fetch FRED data for all series
2. Calculate indicator values
3. Store in SQLite database
4. Export JSON to `frontend/data/`

### Custom Data Sources (Non-FRED)

For data from Yahoo Finance or other sources, override `fetch_and_calculate()`:

```python
def fetch_and_calculate(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> list[DataPoint]:
    """Override to use custom data sources."""
    # Fetch from FRED
    fred_data = self.collector.get_series("GDP", start_date, end_date)

    # Fetch from Yahoo Finance
    from backend.collectors.yahoo_collector import get_wilshire_5000
    yahoo_data = get_wilshire_5000(start_date, end_date)

    # Combine and calculate
    df = pd.DataFrame({"GDP": fred_data, "W5000": yahoo_data})
    df = df.dropna()

    values = self.calculate(df)

    # Convert to DataPoints
    data_points = []
    for date, value in values.items():
        data_points.append(DataPoint(
            indicator_id=self.INDICATOR_ID,
            date=date.strftime("%Y-%m-%d"),
            value=float(value),
            raw_values={"GDP": float(df.loc[date, "GDP"]), ...}
        ))

    return data_points
```

See `buffett_indicator.py` for a complete example.

---

## Frontend Architecture

### Technology Stack
- **No framework** - Vanilla JavaScript
- **Tailwind CSS** + **DaisyUI** - Styling (loaded from CDN)
- **Chart.js** - Visualizations (loaded from CDN)
- **No build process** - Static files served directly

### File Structure

```
frontend/
├── index.html              # Single page app
├── assets/
│   ├── css/
│   │   └── styles.css      # Custom styles (status colors, animations)
│   └── js/
│       ├── app.js          # Main app logic, data loading, UI rendering
│       ├── charts.js       # Chart.js wrapper, sparklines, detail charts
│       └── utils.js        # Formatters, helpers, color mapping
└── data/
    ├── indicators.json     # Summary data (loaded on page init)
    ├── economy/            # Full data files (loaded on modal open)
    │   └── {indicator_id}.json
    └── household/
        └── {indicator_id}.json
```

### Data Flow

1. **Page Load**: `app.js` fetches `data/indicators.json`
2. **Card Rendering**: Each indicator gets a card with sparkline chart
3. **Modal Open**: Full data loaded from `data/{category}/{id}.json`
4. **Detail Chart**: Full historical chart rendered in modal

### Key JavaScript Objects

**App** (`app.js`):
- `App.init()` - Entry point
- `App.loadData()` - Fetches indicators.json
- `App.renderIndicators(category, indicators)` - Renders card grid
- `App.createCard(indicator, category)` - Generates card HTML
- `App.openModal(indicator, category)` - Opens detail modal

**Charts** (`charts.js`):
- `Charts.createSparkline(canvasId, data, status)` - Mini chart on card
- `Charts.createDetailChart(data, indicator)` - Full chart in modal
- `Charts.destroyAll()` - Cleanup chart instances

**Utils** (`utils.js`):
- `Utils.formatNumber(value, unit)` - Number formatting
- `Utils.formatDate(dateStr)` - Date formatting
- `Utils.getStatusColor(status)` - Status to color mapping
- `Utils.fetchJSON(url)` - Fetch with error handling

### JSON Data Structure

**indicators.json** (summary):
```json
{
  "generated_at": "2026-01-19T...",
  "economy": [
    {
      "id": "buffett_indicator",
      "name": "Buffett Indicator",
      "current_value": 215.0,
      "current_date": "2025-07-01",
      "status": "red",           // "green", "yellow", "red"
      "trend": "deteriorating",  // "improving", "stable", "deteriorating"
      "change_value": 11.8,
      "change_percent": 5.81,
      "sparkline": [...]         // Last ~90 data points for mini chart
    }
  ],
  "household": [...]
}
```

**{indicator_id}.json** (full detail):
```json
{
  "id": "buffett_indicator",
  "name": "Buffett Indicator",
  "category": "economy",
  "description": "...",
  "unit": "%",
  "thresholds": {
    "green_max": 100,
    "yellow_max": 150,
    "red_min": 150,
    "invert": false
  },
  "current_value": 215.0,
  "status": "red",
  "trend": "deteriorating",
  "data": [
    {"date": "1989-01-01", "value": 45.2, "raw_values": {...}},
    ...
  ]
}
```

### Status Colors (CSS)

Defined in `styles.css`:
- **Green**: `oklch(var(--su))` - DaisyUI success color
- **Yellow**: `oklch(var(--wa))` - DaisyUI warning color
- **Red**: `oklch(var(--er))` - DaisyUI error color

### Theme Toggle

DaisyUI themes controlled via `data-theme` attribute on `<html>`:
- Light: `data-theme="winter"`
- Dark: `data-theme="night"`
- Persisted in `localStorage.theme`

---

## Database Schema

SQLite database at `data/indicators.db`:

- **indicators** - Indicator metadata (id, name, category, thresholds)
- **data_points** - Time series values (indicator_id, date, value, raw_values)
- **fred_series** - FRED series mappings (indicator_id, series_id, role)
- **update_log** - Update history and errors

---

## Common Tasks

### Find FRED Series IDs
Browse https://fred.stlouisfed.org and copy series ID from URL.

### Test a Calculator
```python
uv run python -c "
from backend.collectors.fred_collector import FredCollector
from backend.db.repository import Repository
from backend.calculators.my_indicator import MyIndicatorCalculator

collector = FredCollector()
repo = Repository('data/indicators.db')
calc = MyIndicatorCalculator(collector, repo)
points = calc.fetch_and_calculate()
print(f'Got {len(points)} data points')
print(f'Latest: {points[-1].date} = {points[-1].value}')
"
```

### Export Only (No Fetch)
```python
from backend.db.repository import Repository
from backend.export.export_json import export_all
export_all(Repository('data/indicators.db'))
```
