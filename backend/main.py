"""Main orchestrator for FedBrrrr data collection and processing."""
import sys
from datetime import datetime

from backend.config import validate_config, DB_PATH
from backend.db.repository import Repository
from backend.collectors.fred_collector import FredCollector
from backend.calculators import ALL_CALCULATORS
from backend.export.export_json import export_all


def run_update(full_refresh: bool = False) -> dict:
    """
    Run a full update of all indicators.

    Args:
        full_refresh: If True, fetch all historical data. If False, only fetch new data.

    Returns:
        Summary of the update operation
    """
    print("=" * 60)
    print(f"FedBrrrr Data Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Validate configuration
    print("\n[1/4] Validating configuration...")
    try:
        validate_config()
        print("  ✓ Configuration valid")
    except ValueError as e:
        print(f"  ✗ Configuration error: {e}")
        sys.exit(1)

    # Initialize database and collector
    print("\n[2/4] Initializing database and FRED connection...")
    repository = Repository(DB_PATH)
    collector = FredCollector()
    print(f"  ✓ Database: {DB_PATH}")
    print("  ✓ FRED API connection ready")

    # Update all indicators
    print(f"\n[3/4] Updating {len(ALL_CALCULATORS)} indicators...")
    results = {
        "success": [],
        "failed": []
    }

    for calculator_class in ALL_CALCULATORS:
        calculator = calculator_class(collector, repository)
        indicator_name = calculator.INDICATOR_NAME

        try:
            count = calculator.update(full_refresh=full_refresh)
            results["success"].append({
                "name": indicator_name,
                "records": count
            })
            print(f"  ✓ {indicator_name}: {count} records")
        except Exception as e:
            results["failed"].append({
                "name": indicator_name,
                "error": str(e)
            })
            print(f"  ✗ {indicator_name}: {e}")

    # Export to JSON
    print("\n[4/4] Exporting data to JSON...")
    try:
        export_result = export_all(repository)
        print(f"  ✓ Exported {export_result['indicators_exported']} indicators")
        print(f"    - Economy: {export_result['economy_count']}")
        print(f"    - Household: {export_result['household_count']}")
    except Exception as e:
        print(f"  ✗ Export failed: {e}")
        results["export_error"] = str(e)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Successful: {len(results['success'])}")
    print(f"  Failed: {len(results['failed'])}")

    if results["failed"]:
        print("\n  Failed indicators:")
        for fail in results["failed"]:
            print(f"    - {fail['name']}: {fail['error']}")

    print("\n" + "=" * 60)

    return results


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="FedBrrrr - Economic Indicators Dashboard")
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="Fetch all historical data (default: incremental update)"
    )

    args = parser.parse_args()

    run_update(full_refresh=args.full_refresh)


if __name__ == "__main__":
    main()
