"""
Dashboard data service — efficient queries for dashboard metrics.
"""
from datetime import datetime, timedelta

from app.database import get_connection
from app.models import RecentActivity
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Provides dashboard summary data via efficient SQL queries."""

    def get_record_summary(self) -> dict:
        """Get active/inactive counts."""
        conn = get_connection()
        row = conn.execute(
            """SELECT
               SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
               SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive
               FROM walkin_records"""
        ).fetchone()
        return {
            "active": row["active"] or 0,
            "inactive": row["inactive"] or 0,
        }

    def get_missing_docs_count(self) -> int:
        """Count active records missing any of the 5 required document types."""
        conn = get_connection()
        from app.constants import DocumentType
        required_types = [dt.value for dt in DocumentType]
        required_count = len(required_types)

        # Records with fewer than 5 distinct document types
        row = conn.execute(
            f"""SELECT COUNT(*) as cnt FROM walkin_records w
               WHERE w.is_active = 1
               AND (
                   SELECT COUNT(DISTINCT d.document_type)
                   FROM documents d WHERE d.record_id = w.id
               ) < ?""",
            (required_count,),
        ).fetchone()
        return row["cnt"] or 0

    def get_expired_visas_count(self) -> int:
        """Count active records with expired visas."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = get_connection()
        row = conn.execute(
            """SELECT COUNT(*) as cnt FROM walkin_records
               WHERE is_active = 1
               AND visa_validity_date != ''
               AND visa_validity_date < ?""",
            (today,),
        ).fetchone()
        return row["cnt"] or 0

    def get_expiring_visas_count(self, days: int = 30) -> int:
        """Count active records with visas expiring within N days."""
        today = datetime.now().strftime("%Y-%m-%d")
        threshold = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        conn = get_connection()
        row = conn.execute(
            """SELECT COUNT(*) as cnt FROM walkin_records
               WHERE is_active = 1
               AND visa_validity_date != ''
               AND visa_validity_date >= ?
               AND visa_validity_date <= ?""",
            (today, threshold),
        ).fetchone()
        return row["cnt"] or 0

    def get_expired_visa_ids(self) -> list[int]:
        """Get IDs of records with expired visas."""
        today = datetime.now().strftime("%Y-%m-%d")
        conn = get_connection()
        rows = conn.execute(
            """SELECT id FROM walkin_records
               WHERE is_active = 1
               AND visa_validity_date != ''
               AND visa_validity_date < ?""",
            (today,),
        ).fetchall()
        return [r["id"] for r in rows]

    def get_expiring_visa_ids(self, days: int = 30) -> list[int]:
        """Get IDs of records with visas expiring within N days."""
        today = datetime.now().strftime("%Y-%m-%d")
        threshold = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        conn = get_connection()
        rows = conn.execute(
            """SELECT id FROM walkin_records
               WHERE is_active = 1
               AND visa_validity_date != ''
               AND visa_validity_date >= ?
               AND visa_validity_date <= ?""",
            (today, threshold),
        ).fetchall()
        return [r["id"] for r in rows]

    # ── Recent Activity ──

    def record_activity(self, record_id: int, action: str):
        """Log a view or edit action."""
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn.execute(
                "INSERT INTO recent_activity (record_id, action, timestamp) VALUES (?, ?, ?)",
                (record_id, action, now),
            )
            # Keep only last 100 entries
            conn.execute(
                """DELETE FROM recent_activity WHERE id NOT IN (
                   SELECT id FROM recent_activity ORDER BY timestamp DESC LIMIT 100
                )"""
            )
            conn.commit()
        except Exception as e:
            logger.warning("Failed to log activity: %s", e)

    def get_recent_activity(self, limit: int = 10) -> list[dict]:
        """Get recent activity with record names."""
        conn = get_connection()
        rows = conn.execute(
            """SELECT ra.id, ra.record_id, ra.action, ra.timestamp,
                      w.first_name, w.last_name
               FROM recent_activity ra
               LEFT JOIN walkin_records w ON w.id = ra.record_id
               ORDER BY ra.timestamp DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Enrollment Trends ──

    def get_enrollment_trends(self, months_back: int = 6) -> dict:
        """Return monthly walk-in counts for the last N months.

        Returns a dict with two keys:
          - 'labels': list[str]  (e.g. ['2024-10', '2024-11', ...])
          - 'values': list[int]  (record counts per month)
        """
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT strftime('%Y-%m', created_at) AS month, COUNT(*) AS cnt
            FROM walkin_records
            WHERE created_at >= date('now', ?)
            GROUP BY month
            ORDER BY month ASC
            """,
            (f"-{months_back} months",),
        ).fetchall()

        # Build a complete month axis so gaps show as 0
        from datetime import date
        today = date.today()
        labels = []
        for i in range(months_back, 0, -1):
            # Go back i months from this month
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1
            labels.append(f"{year}-{month:02d}")

        counts = {r["month"]: r["cnt"] for r in rows}
        values = [counts.get(m, 0) for m in labels]

        return {"labels": labels, "values": values}

    # ── Recently Viewed ──

    def get_recent_profiles(self, limit: int = 5) -> list[dict]:
        """Return the most recently viewed/edited distinct student profiles.

        Each entry: {'record_id': int, 'full_name': str, 'action': str}
        """
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT ra.record_id,
                   w.first_name || ' ' || w.last_name AS full_name,
                   ra.action,
                   MAX(ra.timestamp) AS last_seen
            FROM recent_activity ra
            LEFT JOIN walkin_records w ON w.id = ra.record_id
            WHERE w.id IS NOT NULL AND w.is_active = 1
            GROUP BY ra.record_id
            ORDER BY last_seen DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Stale Records (D2) ──

    def get_stale_records(self, days_threshold: int = 90) -> list:
        """Return active records not updated in the last N days.

        Useful for a dashboard warning card to catch forgotten/outdated records.
        Returns a list of WalkInRecord objects.
        """
        from app.models import WalkInRecord
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT * FROM walkin_records
            WHERE is_active = 1
              AND updated_at <= date('now', ?)
            ORDER BY updated_at ASC
            """,
            (f"-{days_threshold} days",),
        ).fetchall()
        return [WalkInRecord.from_row(dict(r)) for r in rows]

    # ── Enrollment Status Breakdown by Month (D6) ──

    def get_status_breakdown_by_month(self, months_back: int = 6) -> dict:
        """Return per-enrollment-status counts for each of the last N months.

        Returns:
            {
                'labels': ['Sep 2024', 'Oct 2024', ...],
                'series': {'Enrolled': [3, 5, ...], 'Pending': [1, 2, ...], ...}
            }
        """
        from datetime import date
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT strftime('%Y-%m', created_at) AS month,
                   enrollment_status,
                   COUNT(*) AS cnt
            FROM walkin_records
            WHERE created_at >= date('now', ?)
              AND is_active = 1
            GROUP BY month, enrollment_status
            ORDER BY month ASC
            """,
            (f"-{months_back} months",),
        ).fetchall()

        # Build the full month axis (same logic as get_enrollment_trends)
        today = date.today()
        month_labels = []
        for i in range(months_back, 0, -1):
            year = today.year
            m = today.month - i
            while m <= 0:
                m += 12
                year -= 1
            month_labels.append(f"{year}-{m:02d}")

        # Collect unique statuses from data
        statuses = sorted({r["enrollment_status"] for r in rows if r["enrollment_status"]})

        # Pivot: status -> {month -> count}
        pivot: dict[str, dict[str, int]] = {s: {} for s in statuses}
        for r in rows:
            s = r["enrollment_status"]
            if s:
                pivot.setdefault(s, {})[r["month"]] = r["cnt"]

        series = {
            s: [pivot[s].get(m, 0) for m in month_labels]
            for s in statuses
        }
        return {"labels": month_labels, "series": series}
