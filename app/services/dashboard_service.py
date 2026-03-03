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
