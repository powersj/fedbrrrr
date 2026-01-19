"""Export indicator data to JSON for frontend consumption."""
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.config import FRONTEND_DATA_DIR, ECONOMY_DATA_DIR, HOUSEHOLD_DATA_DIR
from backend.db.repository import Repository
from backend.db.models import get_status_from_value


def export_all(repository: Repository) -> dict[str, Any]:
    """
    Export all indicator data to JSON files.

    Creates:
    - frontend/data/indicators.json - Master index of all indicators
    - frontend/data/economy/{indicator_id}.json - Individual economy indicators
    - frontend/data/household/{indicator_id}.json - Individual household indicators

    Returns:
        Summary of export operation
    """
    indicators = repository.get_all_indicators()

    master_index = {
        "generated_at": datetime.now().isoformat(),
        "economy": [],
        "household": []
    }

    export_count = 0

    for indicator in indicators:
        # Get all data points for this indicator
        data_points = repository.get_data_points(indicator.id)

        if not data_points:
            continue

        # Sort by date ascending for time series
        data_points = sorted(data_points, key=lambda x: x.date)

        # Get latest value and calculate status
        latest = data_points[-1]
        status = get_status_from_value(latest.value, indicator.thresholds)

        # Calculate trend (comparing to value from ~1 month ago)
        trend = "stable"
        if len(data_points) > 30:
            month_ago_value = data_points[-30].value
            change = latest.value - month_ago_value
            if abs(change) > 0.01:  # Small threshold to avoid noise
                if indicator.thresholds.invert:
                    # Higher is better
                    trend = "improving" if change > 0 else "deteriorating"
                else:
                    # Lower is better
                    trend = "improving" if change < 0 else "deteriorating"

        # Calculate change from previous period
        change_value = 0.0
        change_percent = 0.0
        if len(data_points) > 1:
            prev_value = data_points[-2].value
            change_value = latest.value - prev_value
            if prev_value != 0:
                change_percent = (change_value / abs(prev_value)) * 100

        # Prepare summary for master index
        summary = {
            "id": indicator.id,
            "name": indicator.name,
            "description": indicator.description,
            "unit": indicator.unit,
            "current_value": round(latest.value, 2),
            "current_date": latest.date,
            "status": status,
            "trend": trend,
            "change_value": round(change_value, 2),
            "change_percent": round(change_percent, 2),
            # Include recent sparkline data (last 90 points)
            "sparkline": [
                {"date": dp.date, "value": round(dp.value, 2)}
                for dp in data_points[-90:]
            ]
        }

        # Add to appropriate category in master index
        if indicator.category == "economy":
            master_index["economy"].append(summary)
            output_dir = ECONOMY_DATA_DIR
        else:
            master_index["household"].append(summary)
            output_dir = HOUSEHOLD_DATA_DIR

        # Create detailed individual file
        detailed_data = {
            "id": indicator.id,
            "name": indicator.name,
            "category": indicator.category,
            "description": indicator.description,
            "unit": indicator.unit,
            "thresholds": {
                "green_max": indicator.thresholds.green_max,
                "green_min": indicator.thresholds.green_min,
                "yellow_max": indicator.thresholds.yellow_max,
                "yellow_min": indicator.thresholds.yellow_min,
                "red_max": indicator.thresholds.red_max,
                "red_min": indicator.thresholds.red_min,
                "invert": indicator.thresholds.invert
            },
            "current_value": round(latest.value, 2),
            "current_date": latest.date,
            "status": status,
            "trend": trend,
            "change_value": round(change_value, 2),
            "change_percent": round(change_percent, 2),
            "data": [
                {
                    "date": dp.date,
                    "value": round(dp.value, 2),
                    "raw_values": {k: round(v, 2) for k, v in dp.raw_values.items()}
                }
                for dp in data_points
            ]
        }

        # Write individual indicator file
        output_path = output_dir / f"{indicator.id}.json"
        with open(output_path, "w") as f:
            json.dump(detailed_data, f, indent=2)

        export_count += 1

    # Write master index
    master_path = FRONTEND_DATA_DIR / "indicators.json"
    with open(master_path, "w") as f:
        json.dump(master_index, f, indent=2)

    return {
        "indicators_exported": export_count,
        "master_index": str(master_path),
        "economy_count": len(master_index["economy"]),
        "household_count": len(master_index["household"])
    }
