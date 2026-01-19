# FedBrrrr.com Implementation Plan

## Project Overview
A static website displaying economic and household financial health indicators with data sourced from FRED API. Backend collects data periodically, stores in SQLite, and exports to static JSON. Frontend is a DaisyUI-based static site hosted on Netlify.

## Technology Stack
- **Backend**: Python 3.11+
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript with DaisyUI (Tailwind CSS)
- **Charts**: Chart.js
- **Hosting**: Netlify
- **Data Updates**: GitHub Actions (scheduled)

## Project Structure
```
fedbrrrr/
├── .github/
│   └── workflows/
│       └── update-data.yml       # GitHub Actions workflow
├── backend/
│   ├── config.py                 # Configuration and API keys
│   ├── main.py                   # Main orchestrator
│   ├── requirements.txt          # Python dependencies
│   ├── db/
│   │   ├── schema.sql           # SQLite schema
│   │   ├── models.py            # Data models
│   │   └── repository.py        # Data access layer
│   ├── collectors/
│   │   └── fred_collector.py    # FRED API collector
│   ├── calculators/
│   │   ├── base.py              # Base calculator class
│   │   ├── buffett_indicator.py
│   │   ├── yield_curves.py
│   │   ├── sahm_rule.py
│   │   ├── mortgage_affordability.py
│   │   └── real_wage_growth.py
│   └── export/
│       └── export_json.py       # Export SQLite to JSON
├── frontend/
│   ├── index.html               # Main page
│   ├── data/                    # Generated JSON files (gitignored except structure)
│   │   ├── indicators.json      # Main index
│   │   ├── economy/
│   │   │   └── *.json          # Individual indicator files
│   │   └── household/
│   │       └── *.json          # Individual indicator files
│   ├── assets/
│   │   ├── css/
│   │   │   └── styles.css      # Custom styles
│   │   └── js/
│   │       ├── app.js          # Main application logic
│   │       ├── charts.js       # Chart rendering
│   │       └── utils.js        # Helper functions
│   └── netlify.toml             # Netlify configuration
├── data/
│   └── indicators.db            # SQLite database (gitignored)
├── .gitignore
└── README.md
```

## Database Schema

### indicators table
```sql
CREATE TABLE indicators (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,           -- 'economy' or 'household'
    description TEXT,
    interpretation_direction TEXT,     -- 'higher_is_better', 'lower_is_better', 'neutral'
    threshold_good REAL,
    threshold_warning REAL,
    threshold_bad REAL,
    calculation_type TEXT,             -- 'direct', 'calculated', 'ratio', 'difference'
    update_frequency TEXT,             -- 'daily', 'monthly', 'quarterly'
    enabled BOOLEAN DEFAULT 1
);

CREATE TABLE fred_series (
    indicator_id TEXT NOT NULL,
    series_id TEXT NOT NULL,
    series_name TEXT,
    role TEXT,                         -- 'primary', 'numerator', 'denominator', 'component'
    PRIMARY KEY (indicator_id, series_id),
    FOREIGN KEY (indicator_id) REFERENCES indicators(id)
);

CREATE TABLE data_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id TEXT NOT NULL,
    date TEXT NOT NULL,
    value REAL NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (indicator_id) REFERENCES indicators(id),
    UNIQUE(indicator_id, date)
);

CREATE INDEX idx_data_points_indicator_date ON data_points(indicator_id, date DESC);

CREATE TABLE update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id TEXT,
    status TEXT,                       -- 'success', 'error', 'skipped'
    message TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Indicators Configuration

### Economy Category
1. **Buffett Indicator** (Market Cap / GDP)
   - FRED: WILSHIRE5000PRFC / GDP
   - Lower is better
   - Thresholds: Good <100, Warning 100-140, Bad >140

2. **10Y-2Y Yield Curve**
   - FRED: DGS10 - DGS2
   - Interpretation: Inversion (negative) warns of recession
   - Thresholds: Good >0.5, Warning 0 to 0.5, Bad <0

3. **10Y-3M Yield Curve**
   - FRED: DGS10 - DGS3MO
   - Same interpretation as 10Y-2Y

4. **Sahm Rule**
   - FRED: UNRATE
   - Calculated: 3-month moving average vs 12-month low
   - Threshold: >0.5 indicates recession

5. **Fed Balance Sheet Growth** (YoY %)
   - FRED: WALCL
   - Neutral interpretation
   - Shows QE/QT activity

6. **M2 Money Supply Growth** (YoY %)
   - FRED: M2SL
   - Higher growth can indicate inflation risk
   - Thresholds: Good 2-4%, Warning 4-8%, Bad >8%

7. **Consumer Confidence Index**
   - FRED: UMCSENT (University of Michigan)
   - Higher is better
   - Thresholds: Good >90, Warning 70-90, Bad <70

### Household Category
1. **Mortgage Affordability Index**
   - FRED: MORTGAGE30US, MSPUS (median sales price), MEHOINUSA646N (median household income)
   - Calculate: Monthly payment as % of median income
   - Lower is better
   - Thresholds: Good <28%, Warning 28-35%, Bad >35%

2. **Credit Card Delinquency Rate**
   - FRED: DRCCLACBS
   - Lower is better
   - Thresholds: Good <2%, Warning 2-3%, Bad >3%

3. **Household Debt Service Ratio**
   - FRED: TDSP
   - Lower is better
   - Thresholds: Good <10%, Warning 10-12%, Bad >12%

4. **Real Wage Growth** (YoY %)
   - FRED: CES0500000003 (avg hourly earnings), CPIAUCSL (CPI)
   - Calculate: Nominal wage growth - inflation
   - Higher is better
   - Thresholds: Good >2%, Warning 0-2%, Bad <0%

5. **Personal Savings Rate**
   - FRED: PSAVERT
   - Higher is better
   - Thresholds: Good >8%, Warning 5-8%, Bad <5%

6. **Rent Burden Ratio**
   - FRED: CUUR0000SEHA (rent index), MEHOINUSA646N (median income)
   - Calculate: Median rent as % of income
   - Lower is better
   - Thresholds: Good <30%, Warning 30-40%, Bad >40%

7. **Food Price Burden**
   - FRED: CPIUFDSL (food CPI), MEHOINUSA646N
   - Calculate: Food cost as % of income
   - Lower is better
   - Thresholds: Good <10%, Warning 10-15%, Bad >15%

## Backend Implementation Details

### config.py
```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    FRED_API_KEY: str
    DATABASE_PATH: str = "data/indicators.db"
    JSON_OUTPUT_DIR: str = "frontend/data"
    LOOKBACK_YEARS: int = 10  # How much historical data to fetch
    
    @classmethod
    def from_env(cls):
        return cls(
            FRED_API_KEY=os.getenv("FRED_API_KEY", ""),
        )
```

### main.py
```python
# Orchestrates data collection and export
# 1. Initialize database if needed
# 2. For each enabled indicator:
#    - Determine last data point date
#    - Fetch new data from FRED
#    - Calculate derived indicators
#    - Store in SQLite
# 3. Call export_json.py
# 4. Log results
```

### collectors/fred_collector.py
```python
# Responsibilities:
# - Fetch data from FRED API
# - Handle rate limiting
# - Parse responses
# - Return standardized data format
# - Support date range queries (fetch only new data)
```

### calculators/base.py
```python
# Base class for all calculators
# - Define interface for calculate() method
# - Handle data fetching from repository
# - Standardize output format
```

### Individual calculator files
Each calculator implements:
- Fetch required series data
- Perform calculation
- Return time series of calculated values
- Handle missing data gracefully

### export/export_json.py
```python
# Responsibilities:
# 1. Read all indicators from SQLite
# 2. For each indicator:
#    - Get last 10 years of data
#    - Calculate current status (good/warning/bad)
#    - Calculate trend (direction and % change)
#    - Determine 3-month, 6-month, 1-year changes
# 3. Export individual JSON files per indicator
# 4. Export master indicators.json index file
# 5. Include metadata: last_updated, data freshness
```

### JSON Output Format

**frontend/data/indicators.json:**
```json
{
  "last_updated": "2025-01-19T12:00:00Z",
  "categories": {
    "economy": [
      {
        "id": "buffett-indicator",
        "name": "Buffett Indicator",
        "description": "Total market cap relative to GDP",
        "current_value": 195.2,
        "current_date": "2024-12-31",
        "status": "bad",
        "trend": "up",
        "change_1m": 2.1,
        "change_3m": 5.2,
        "change_6m": 8.3,
        "change_1y": 12.1,
        "interpretation": "Higher values indicate overvalued market",
        "data_file": "economy/buffett-indicator.json"
      }
    ],
    "household": [...]
  }
}
```

**frontend/data/economy/buffett-indicator.json:**
```json
{
  "id": "buffett-indicator",
  "name": "Buffett Indicator",
  "description": "Total market capitalization to GDP ratio, popularized by Warren Buffett as a market valuation metric",
  "category": "economy",
  "interpretation": {
    "direction": "lower_is_better",
    "explanation": "Values above 100 suggest overvaluation, with extreme overvaluation above 140",
    "thresholds": {
      "good": 100,
      "warning": 140,
      "bad": 170
    }
  },
  "current": {
    "value": 195.2,
    "date": "2024-12-31",
    "status": "bad"
  },
  "history": [
    {"date": "2024-12-31", "value": 195.2},
    {"date": "2024-09-30", "value": 192.1},
    {"date": "2024-06-30", "value": 189.5},
    ...
  ],
  "sources": [
    {"name": "Wilshire 5000", "fred_id": "WILSHIRE5000PRFC"},
    {"name": "GDP", "fred_id": "GDP"}
  ]
}
```

## Frontend Implementation

### index.html Structure
```html
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FedBrrrr - Economic Reality Check</title>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.6.0/dist/full.min.css" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body>
    <!-- Hero Section -->
    <div class="hero min-h-[40vh] bg-base-200">
        <div class="hero-content text-center">
            <div class="max-w-md">
                <h1 class="text-5xl font-bold">FedBrrrr 💸</h1>
                <p class="py-6">Economic reality check: What the Fed's money printer means for your wallet</p>
                <p class="text-sm opacity-60" id="last-updated">Last updated: ...</p>
            </div>
        </div>
    </div>

    <!-- Economy Section -->
    <section class="container mx-auto px-4 py-8">
        <h2 class="text-3xl font-bold mb-6">📊 The Economy</h2>
        <div id="economy-indicators" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Indicator cards loaded here -->
        </div>
    </section>

    <!-- Household Section -->
    <section class="container mx-auto px-4 py-8">
        <h2 class="text-3xl font-bold mb-6">🏠 Your Household</h2>
        <div id="household-indicators" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- Indicator cards loaded here -->
        </div>
    </section>

    <!-- Modal for detailed view -->
    <dialog id="detail-modal" class="modal">
        <div class="modal-box w-11/12 max-w-5xl">
            <form method="dialog">
                <button class="btn btn-sm btn-circle btn-ghost absolute right-2 top-2">✕</button>
            </form>
            <h3 class="font-bold text-lg" id="modal-title"></h3>
            <p class="py-2" id="modal-description"></p>
            <div class="py-4">
                <canvas id="detail-chart"></canvas>
            </div>
            <div id="modal-sources" class="text-sm opacity-60 mt-4"></div>
        </div>
    </dialog>

    <script src="assets/js/utils.js"></script>
    <script src="assets/js/charts.js"></script>
    <script src="assets/js/app.js"></script>
</body>
</html>
```

### DaisyUI Indicator Card Component
```html
<!-- Example card structure -->
<div class="card bg-base-100 shadow-xl hover:shadow-2xl transition-shadow cursor-pointer">
    <div class="card-body">
        <div class="flex justify-between items-start">
            <h3 class="card-title text-lg">Buffett Indicator</h3>
            <div class="badge badge-error">Bad</div>
        </div>
        
        <div class="flex items-baseline gap-2 my-2">
            <span class="text-3xl font-bold">195.2</span>
            <span class="text-sm opacity-60">% of GDP</span>
        </div>
        
        <div class="flex gap-2 text-sm">
            <span class="badge badge-outline">
                <span class="text-error">↑ 12.1%</span> 1Y
            </span>
            <span class="badge badge-outline">
                <span class="text-error">↑ 5.2%</span> 3M
            </span>
        </div>
        
        <!-- Mini sparkline -->
        <div class="mt-2 h-12">
            <canvas class="sparkline"></canvas>
        </div>
        
        <p class="text-sm opacity-70 mt-2">
            Market significantly overvalued relative to economy
        </p>
        
        <div class="card-actions justify-end mt-2">
            <button class="btn btn-sm btn-ghost">View Details →</button>
        </div>
    </div>
</div>
```

### assets/js/app.js
```javascript
// Responsibilities:
// 1. Load indicators.json on page load
// 2. Render indicator cards for each category
// 3. Create sparkline charts for each card
// 4. Handle card clicks to show detail modal
// 5. Update "last updated" timestamp
```

### assets/js/charts.js
```javascript
// Responsibilities:
// 1. Create sparkline charts (minimal, no axes)
// 2. Create detailed modal charts (full featured)
// 3. Apply color coding based on status
// 4. Handle responsive sizing
```

### assets/js/utils.js
```javascript
// Helper functions:
// - formatNumber(value, decimals)
// - formatPercent(value)
// - formatDate(dateString)
// - getStatusColor(status) -> returns DaisyUI color class
// - getTrendIcon(trend) -> returns ↑ or ↓
// - calculateChange(current, previous)
```

### assets/css/styles.css
```css
/* Custom styles beyond DaisyUI */
/* - Sparkline canvas sizing */
/* - Card hover effects */
/* - Status badge colors */
/* - Chart container responsive styling */
```

## GitHub Actions Workflow

**.github/workflows/update-data.yml:**
```yaml
name: Update Economic Data

on:
  schedule:
    # Run every Monday and Thursday at 2 PM UTC (after markets close)
    - cron: '0 14 * * 1,4'
  workflow_dispatch:  # Allow manual triggers

jobs:
  update:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
      
      - name: Create data directory
        run: mkdir -p data
      
      - name: Fetch and process data
        env:
          FRED_API_KEY: ${{ secrets.FRED_API_KEY }}
        run: |
          cd backend
          python main.py
      
      - name: Export to JSON
        run: |
          cd backend
          python export/export_json.py
      
      - name: Commit updated data
        run: |
          git config user.name "Economic Data Bot"
          git config user.email "bot@fedbrrrr.com"
          git add frontend/data/
          git add data/indicators.db
          git diff --quiet && git diff --staged --quiet || (
            git commit -m "📊 Update economic data - $(date +'%Y-%m-%d %H:%M UTC')"
            git push
          )
```

## Netlify Configuration

**netlify.toml:**
```toml
[build]
  publish = "frontend"
  command = "echo 'No build needed - static site'"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/data/*"
  [headers.values]
    Cache-Control = "public, max-age=3600"  # Cache JSON for 1 hour

[[headers]]
  for = "/*.html"
  [headers.values]
    Cache-Control = "public, max-age=0, must-revalidate"

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

## .gitignore
```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# Database
data/indicators.db
data/indicators.db-journal

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Don't ignore JSON structure
!frontend/data/.gitkeep
frontend/data/**/*.json
```

## Dependencies

**backend/requirements.txt:**
```
fredapi==0.5.1
requests==2.31.0
python-dateutil==2.8.2
```

## Implementation Steps

1. **Initialize Project Structure**
   - Create directory structure
   - Set up git repository
   - Create .gitignore

2. **Database Setup**
   - Create schema.sql
   - Create models.py with data classes
   - Create repository.py for data access
   - Seed indicators table with configuration

3. **Backend - FRED Collector**
   - Implement fred_collector.py
   - Test API connectivity
   - Implement date range queries

4. **Backend - Calculators**
   - Implement base calculator class
   - Implement each calculator one by one
   - Test calculations with sample data

5. **Backend - Main Orchestrator**
   - Implement main.py to coordinate collection
   - Add error handling and logging
   - Test full collection cycle

6. **Backend - JSON Export**
   - Implement export_json.py
   - Test JSON output format
   - Verify file structure

7. **Frontend - Base HTML**
   - Create index.html with DaisyUI
   - Set up sections and layout
   - Add modal structure

8. **Frontend - JavaScript**
   - Implement utils.js helpers
   - Implement charts.js for Chart.js integration
   - Implement app.js for main logic
   - Test with sample JSON data

9. **Frontend - Styling**
   - Add custom CSS
   - Ensure responsive design
   - Test on mobile

10. **GitHub Actions**
    - Create workflow file
    - Set up FRED_API_KEY secret
    - Test manual trigger
    - Verify automatic updates

11. **Netlify Deployment**
    - Connect repository to Netlify
    - Configure build settings
    - Test deployment
    - Verify auto-deploy on commits

## Testing Checklist

- [ ] Database schema creates successfully
- [ ] FRED API connection works
- [ ] Each calculator produces correct results
- [ ] JSON export creates proper file structure
- [ ] Frontend loads and displays all indicators
- [ ] Status badges show correct colors
- [ ] Sparklines render properly
- [ ] Modal opens with detailed charts
- [ ] Responsive design works on mobile
- [ ] GitHub Action runs successfully
- [ ] Netlify deploys correctly
- [ ] Auto-updates work on schedule

## Future Enhancements (Post-MVP)

- Historical comparison tool ("Compare to 2008 crisis")
- Downloadable data exports (CSV)
- RSS feed for indicator threshold crossings
- Email alerts for major changes
- Composite "economy health score"
- Share individual indicator cards as images
- Dark mode support
- Indicator explanations/education section

---

This plan should give Claude Code everything needed to build the complete system. Start with the backend database and collection logic, then move to the export and frontend rendering.
