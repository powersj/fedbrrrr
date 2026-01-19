# FedBrrrr

Economic and household financial health indicators dashboard using FRED data.

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- FRED API key (free at https://fred.stlouisfed.org/docs/api/api_key.html)

### Installation

```bash
# Install dependencies
uv sync

# Create .env file with your FRED API key
echo "FRED_API_KEY=your_api_key_here" > .env
```

## Running the Backend

The backend fetches data from FRED (and Yahoo Finance for Wilshire 5000), calculates indicators, and exports JSON files for the frontend.

```bash
# Incremental update (only fetch new data)
uv run python -m backend.main

# Full refresh (fetch all historical data)
uv run python -m backend.main --full-refresh
```

Data is stored in:
- `data/indicators.db` - SQLite database
- `frontend/data/` - JSON files for the frontend

## Running the Frontend

The frontend is a static site with no build process. Serve it with any HTTP server:

```bash
# Using Python
cd frontend && python3 -m http.server 8080

# Using Node.js
npx serve frontend

# Using PHP
php -S localhost:8080 -t frontend
```

Then open http://localhost:8080 in your browser.

## Project Structure

```
fedbrrrr/
├── backend/
│   ├── calculators/     # Indicator calculation logic
│   ├── collectors/      # Data fetching (FRED, Yahoo Finance)
│   ├── db/              # Database models and repository
│   ├── export/          # JSON export for frontend
│   ├── config.py        # Configuration
│   └── main.py          # CLI entry point
├── frontend/
│   ├── index.html       # Main page
│   ├── assets/          # CSS and JavaScript
│   └── data/            # Generated JSON data
├── data/                # SQLite database
└── pyproject.toml       # Python dependencies
```

## Indicators

### Economy (7)
- Buffett Indicator - Stock market cap to GDP ratio
- Yield Curve (10Y-2Y) - Treasury spread
- Yield Curve (10Y-3M) - Treasury spread
- Sahm Rule - Recession indicator
- Fed Balance Sheet - Federal Reserve assets
- M2 Money Supply Growth - Money supply changes
- Consumer Confidence - Sentiment index

### Household (7)
- Mortgage Affordability - Payment as % of income
- Credit Card Delinquency - 90+ days past due
- Debt Service Ratio - Household debt obligations
- Real Wage Growth - Inflation-adjusted wages
- Personal Savings Rate - Household savings
- Rent Burden Index - Rent as % of income
- Food Burden Index - Food spending as % of income
