"""Data access layer for FedBrrrr."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from .models import Indicator, FredSeries, DataPoint, UpdateLog, Thresholds


class Repository:
    """Repository for database operations."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize the database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            schema = f.read()

        with self._get_connection() as conn:
            conn.executescript(schema)

    # Indicator operations
    def upsert_indicator(self, indicator: Indicator) -> None:
        """Insert or update an indicator."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO indicators (id, name, category, description, unit, thresholds_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    category = excluded.category,
                    description = excluded.description,
                    unit = excluded.unit,
                    thresholds_json = excluded.thresholds_json,
                    updated_at = excluded.updated_at
            """, (
                indicator.id,
                indicator.name,
                indicator.category,
                indicator.description,
                indicator.unit,
                indicator.thresholds.to_json(),
                datetime.now().isoformat()
            ))

    def get_indicator(self, indicator_id: str) -> Optional[Indicator]:
        """Get an indicator by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM indicators WHERE id = ?", (indicator_id,)
            ).fetchone()

            if row:
                return Indicator(
                    id=row["id"],
                    name=row["name"],
                    category=row["category"],
                    description=row["description"],
                    unit=row["unit"],
                    thresholds=Thresholds.from_json(row["thresholds_json"]) if row["thresholds_json"] else Thresholds(),
                )
            return None

    def get_all_indicators(self) -> list[Indicator]:
        """Get all indicators."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM indicators ORDER BY category, name").fetchall()
            return [
                Indicator(
                    id=row["id"],
                    name=row["name"],
                    category=row["category"],
                    description=row["description"],
                    unit=row["unit"],
                    thresholds=Thresholds.from_json(row["thresholds_json"]) if row["thresholds_json"] else Thresholds(),
                )
                for row in rows
            ]

    # FRED series operations
    def add_fred_series(self, series: FredSeries) -> None:
        """Add a FRED series mapping."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO fred_series (indicator_id, series_id, role)
                VALUES (?, ?, ?)
            """, (series.indicator_id, series.series_id, series.role))

    def get_fred_series(self, indicator_id: str) -> list[FredSeries]:
        """Get all FRED series for an indicator."""
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM fred_series WHERE indicator_id = ?", (indicator_id,)
            ).fetchall()
            return [
                FredSeries(
                    indicator_id=row["indicator_id"],
                    series_id=row["series_id"],
                    role=row["role"]
                )
                for row in rows
            ]

    # Data point operations
    def upsert_data_point(self, data_point: DataPoint) -> None:
        """Insert or update a data point."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO data_points (indicator_id, date, value, raw_values_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(indicator_id, date) DO UPDATE SET
                    value = excluded.value,
                    raw_values_json = excluded.raw_values_json
            """, (
                data_point.indicator_id,
                data_point.date,
                data_point.value,
                json.dumps(data_point.raw_values)
            ))

    def upsert_data_points(self, data_points: list[DataPoint]) -> int:
        """Insert or update multiple data points. Returns count of rows affected."""
        with self._get_connection() as conn:
            for dp in data_points:
                conn.execute("""
                    INSERT INTO data_points (indicator_id, date, value, raw_values_json)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(indicator_id, date) DO UPDATE SET
                        value = excluded.value,
                        raw_values_json = excluded.raw_values_json
                """, (
                    dp.indicator_id,
                    dp.date,
                    dp.value,
                    json.dumps(dp.raw_values)
                ))
            return len(data_points)

    def get_data_points(
        self,
        indicator_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> list[DataPoint]:
        """Get data points for an indicator, optionally filtered by date range."""
        query = "SELECT * FROM data_points WHERE indicator_id = ?"
        params: list = [indicator_id]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        query += " ORDER BY date DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                DataPoint(
                    id=row["id"],
                    indicator_id=row["indicator_id"],
                    date=row["date"],
                    value=row["value"],
                    raw_values=json.loads(row["raw_values_json"]) if row["raw_values_json"] else {}
                )
                for row in rows
            ]

    def get_latest_data_point(self, indicator_id: str) -> Optional[DataPoint]:
        """Get the most recent data point for an indicator."""
        points = self.get_data_points(indicator_id, limit=1)
        return points[0] if points else None

    def get_latest_date(self, indicator_id: str) -> Optional[str]:
        """Get the most recent date for an indicator's data."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT MAX(date) as max_date FROM data_points WHERE indicator_id = ?",
                (indicator_id,)
            ).fetchone()
            return row["max_date"] if row else None

    # Update log operations
    def log_update_start(self, indicator_id: str) -> int:
        """Log the start of an update operation. Returns the log ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO update_log (indicator_id, status, started_at)
                VALUES (?, 'success', ?)
            """, (indicator_id, datetime.now().isoformat()))
            return cursor.lastrowid

    def log_update_complete(self, log_id: int, records_added: int) -> None:
        """Log successful completion of an update."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE update_log
                SET status = 'success', records_added = ?, completed_at = ?
                WHERE id = ?
            """, (records_added, datetime.now().isoformat(), log_id))

    def log_update_error(self, log_id: int, error_message: str) -> None:
        """Log an error during update."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE update_log
                SET status = 'error', error_message = ?, completed_at = ?
                WHERE id = ?
            """, (error_message, datetime.now().isoformat(), log_id))

    def get_recent_updates(self, indicator_id: str, limit: int = 10) -> list[UpdateLog]:
        """Get recent update logs for an indicator."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM update_log
                WHERE indicator_id = ?
                ORDER BY started_at DESC
                LIMIT ?
            """, (indicator_id, limit)).fetchall()
            return [
                UpdateLog(
                    id=row["id"],
                    indicator_id=row["indicator_id"],
                    status=row["status"],
                    records_added=row["records_added"],
                    error_message=row["error_message"],
                )
                for row in rows
            ]
