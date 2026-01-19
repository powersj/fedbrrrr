-- FedBrrrr Database Schema

-- Indicators metadata table
CREATE TABLE IF NOT EXISTS indicators (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('economy', 'household')),
    description TEXT,
    unit TEXT,
    thresholds_json TEXT,  -- JSON object with threshold definitions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FRED series mapping table
CREATE TABLE IF NOT EXISTS fred_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id TEXT NOT NULL,
    series_id TEXT NOT NULL,  -- FRED series ID (e.g., 'GDP', 'WILSHIRE5000PRFC')
    role TEXT NOT NULL,  -- Role in calculation (e.g., 'numerator', 'denominator', 'primary')
    FOREIGN KEY (indicator_id) REFERENCES indicators(id),
    UNIQUE (indicator_id, series_id, role)
);

-- Raw data points from FRED
CREATE TABLE IF NOT EXISTS data_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id TEXT NOT NULL,
    date TEXT NOT NULL,  -- ISO date format YYYY-MM-DD
    value REAL NOT NULL,
    raw_values_json TEXT,  -- JSON object with component values used in calculation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (indicator_id) REFERENCES indicators(id),
    UNIQUE (indicator_id, date)
);

-- Update log for tracking data fetches
CREATE TABLE IF NOT EXISTS update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'error')),
    records_added INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (indicator_id) REFERENCES indicators(id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_data_points_indicator_date ON data_points(indicator_id, date);
CREATE INDEX IF NOT EXISTS idx_update_log_indicator ON update_log(indicator_id, started_at);
