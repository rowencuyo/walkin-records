"""
Notification service — scan, create, group, lifecycle management.
"""
from datetime import datetime, timedelta

from app.database import get_connection, DATA_DIR
from app.models import Notification
from app.constants import (
    NotificationSeverity, NotificationCategory, NotificationStatus,
)
from app.services.preferences_service import PreferencesService
from app.utils.logger import get_logger

logger = get_logger(__name__)

BACKUP_META_FILE = DATA_DIR / "backup_meta.json"


class NotificationService:
    """Manages notification lifecycle: scan, CRUD, grouping, cleanup."""

    def __init__(self):
        self._prefs = PreferencesService()

    # ── Scan & Generate ──

    def scan_and_generate(self):
        """Scan records for conditions and create notifications."""
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().strftime("%Y-%m-%d")
        threshold_days = self._prefs.get_int("visa_expiry_threshold_days", 30)
        threshold_date = (datetime.now() + timedelta(days=threshold_days)).strftime("%Y-%m-%d")

        # ── Expired visas ──
        if self._prefs.get_bool("notify_visa_expiry"):
            expired = conn.execute(
                """SELECT id, first_name, last_name, visa_validity_date
                   FROM walkin_records
                   WHERE is_active = 1 AND visa_validity_date != '' AND visa_validity_date < ?""",
                (today,),
            ).fetchall()
            for r in expired:
                group_key = f"visa_expiry_{r['id']}"
                if not self._notification_exists(group_key):
                    self._create(
                        severity=NotificationSeverity.CRITICAL.value,
                        category=NotificationCategory.VISA_EXPIRY.value,
                        title="Visa Expired",
                        message=f"{r['first_name']} {r['last_name']} — visa expired on {r['visa_validity_date']}",
                        group_key=group_key,
                        record_id=r["id"],
                        created_at=now,
                    )

        # ── Expiring visas ──
        if self._prefs.get_bool("notify_visa_expiry"):
            expiring = conn.execute(
                """SELECT id, first_name, last_name, visa_validity_date
                   FROM walkin_records
                   WHERE is_active = 1 AND visa_validity_date != ''
                   AND visa_validity_date >= ? AND visa_validity_date <= ?""",
                (today, threshold_date),
            ).fetchall()
            for r in expiring:
                group_key = f"visa_expiring_{r['id']}"
                if not self._notification_exists(group_key):
                    self._create(
                        severity=NotificationSeverity.WARNING.value,
                        category=NotificationCategory.VISA_EXPIRING.value,
                        title="Visa Expiring Soon",
                        message=f"{r['first_name']} {r['last_name']} — visa expires {r['visa_validity_date']}",
                        group_key=group_key,
                        record_id=r["id"],
                        created_at=now,
                    )

        # ── Missing documents ──
        if self._prefs.get_bool("notify_missing_docs"):
            from app.constants import DocumentType
            required_count = len(DocumentType)
            missing = conn.execute(
                f"""SELECT w.id, w.first_name, w.last_name
                   FROM walkin_records w
                   WHERE w.is_active = 1
                   AND (SELECT COUNT(DISTINCT d.document_type) FROM documents d WHERE d.record_id = w.id) < ?""",
                (required_count,),
            ).fetchall()
            for r in missing:
                group_key = f"missing_docs_{r['id']}"
                if not self._notification_exists(group_key):
                    self._create(
                        severity=NotificationSeverity.WARNING.value,
                        category=NotificationCategory.MISSING_DOCS.value,
                        title="Incomplete Documents",
                        message=f"{r['first_name']} {r['last_name']} — missing required documents",
                        group_key=group_key,
                        record_id=r["id"],
                        created_at=now,
                    )

        # ── Backup overdue ──
        if self._prefs.get_bool("notify_backup_reminder"):
            import json
            backup_overdue = True
            try:
                if BACKUP_META_FILE.exists():
                    with open(BACKUP_META_FILE, "r") as f:
                        meta = json.load(f)
                    last = datetime.fromisoformat(meta.get("last_backup", ""))
                    if (datetime.now() - last).days < 7:
                        backup_overdue = False
            except Exception:
                pass

            group_key = "backup_overdue"
            if backup_overdue and not self._notification_exists(group_key):
                self._create(
                    severity=NotificationSeverity.INFO.value,
                    category=NotificationCategory.BACKUP_OVERDUE.value,
                    title="Backup Reminder",
                    message="No backup has been created in the last 7 days",
                    group_key=group_key,
                    record_id=None,
                    created_at=now,
                )
            elif not backup_overdue:
                # Auto-resolve
                self._resolve_by_group(group_key, now)

        # ── Auto-resolve resolved conditions ──
        self._auto_resolve_visas(today, now)

        # ── Cleanup old notifications ──
        retention = self._prefs.get_int("notification_retention_days", 90)
        self._cleanup_old(retention)

    # ── CRUD ──

    def get_notifications(
        self,
        status_filter: str = "",
        severity_filter: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> list[Notification]:
        conn = get_connection()
        conditions = []
        params = []

        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)
        if severity_filter:
            conditions.append("severity = ?")
            params.append(severity_filter)

        where = " AND ".join(conditions) if conditions else "1=1"
        rows = conn.execute(
            f"""SELECT * FROM notifications WHERE {where}
               ORDER BY
                 CASE severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
                 created_at DESC
               LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()
        return [Notification.from_row(dict(r)) for r in rows]

    def get_active_notifications(self, limit: int = 50) -> list[Notification]:
        """Get unread + read notifications (not dismissed/resolved)."""
        conn = get_connection()
        rows = conn.execute(
            """SELECT * FROM notifications
               WHERE status IN ('unread', 'read')
               ORDER BY
                 CASE severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END,
                 created_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [Notification.from_row(dict(r)) for r in rows]

    def get_unread_count(self) -> int:
        conn = get_connection()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM notifications WHERE status = 'unread'"
        ).fetchone()
        return row["cnt"] or 0

    def mark_read(self, notification_id: int):
        conn = get_connection()
        conn.execute(
            "UPDATE notifications SET status = 'read' WHERE id = ? AND status = 'unread'",
            (notification_id,),
        )
        conn.commit()

    def mark_dismissed(self, notification_id: int):
        conn = get_connection()
        conn.execute(
            "UPDATE notifications SET status = 'dismissed' WHERE id = ?",
            (notification_id,),
        )
        conn.commit()

    def mark_all_read(self):
        conn = get_connection()
        conn.execute("UPDATE notifications SET status = 'read' WHERE status = 'unread'")
        conn.commit()

    # ── Helpers ──

    def _notification_exists(self, group_key: str) -> bool:
        conn = get_connection()
        row = conn.execute(
            "SELECT id FROM notifications WHERE group_key = ? AND status IN ('unread', 'read')",
            (group_key,),
        ).fetchone()
        return row is not None

    def _create(self, severity, category, title, message, group_key, record_id, created_at):
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO notifications
                   (severity, category, title, message, group_key, record_id, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, 'unread', ?)""",
                (severity, category, title, message, group_key, record_id, created_at),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Failed to create notification: %s", e)

    def _resolve_by_group(self, group_key: str, now: str):
        conn = get_connection()
        conn.execute(
            "UPDATE notifications SET status = 'resolved', resolved_at = ? WHERE group_key = ? AND status IN ('unread', 'read')",
            (now, group_key),
        )
        conn.commit()

    def _auto_resolve_visas(self, today: str, now: str):
        """Auto-resolve visa notifications for records that are no longer active or whose visa was updated."""
        conn = get_connection()
        # Find visa_expiry notifications where visa is no longer expired
        conn.execute(
            """UPDATE notifications SET status = 'resolved', resolved_at = ?
               WHERE category = 'visa_expiry' AND status IN ('unread', 'read')
               AND record_id IS NOT NULL
               AND record_id NOT IN (
                   SELECT id FROM walkin_records
                   WHERE is_active = 1 AND visa_validity_date != '' AND visa_validity_date < ?
               )""",
            (now, today),
        )
        conn.commit()

    def _cleanup_old(self, retention_days: int):
        """Remove notifications older than retention period that are resolved/dismissed."""
        cutoff = (datetime.now() - timedelta(days=retention_days)).strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        conn.execute(
            "DELETE FROM notifications WHERE status IN ('resolved', 'dismissed') AND created_at < ?",
            (cutoff,),
        )
        conn.commit()
