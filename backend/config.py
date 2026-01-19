"""Configuration loading from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# FRED API Configuration
FRED_API_KEY = os.getenv("FRED_API_KEY")

# Database Configuration
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "indicators.db"

# Frontend data export paths
FRONTEND_DATA_DIR = PROJECT_ROOT / "frontend" / "data"
ECONOMY_DATA_DIR = FRONTEND_DATA_DIR / "economy"
HOUSEHOLD_DATA_DIR = FRONTEND_DATA_DIR / "household"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
FRONTEND_DATA_DIR.mkdir(exist_ok=True)
ECONOMY_DATA_DIR.mkdir(exist_ok=True)
HOUSEHOLD_DATA_DIR.mkdir(exist_ok=True)


def validate_config() -> bool:
    """Validate that required configuration is present."""
    if not FRED_API_KEY:
        raise ValueError(
            "FRED_API_KEY environment variable is not set. "
            "Get your API key at https://fred.stlouisfed.org/docs/api/api_key.html"
        )
    return True
