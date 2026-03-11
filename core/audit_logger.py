"""
Centralized audit logging system.
Logs all significant user actions to the audit_logs SQLite table.
"""
from datetime import datetime
from app.database import get_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)


def log_action(
    user: str,
    action: str,
    module: str,
    record_id: int | None = None,
    details: str | None = None,
):
    """
    Write an audit log entry.

    Parameters
    ----------
    user : str
        The username performing the action (e.g. 'admin').
    action : str
        A short action code, e.g. CREATE_RECORD, EDIT_RECORD, DELETE_RECORD,
        LOGIN, LOGOUT, UPDATE_SETTINGS.
    module : str
        The application module or page, e.g. 'records', 'auth', 'settings'.
    record_id : int | None
        The ID of the affected record, if applicable.
    details : str | None
        Optional human-readable details about the action.
    """
    conn = get_connection()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            """INSERT INTO audit_logs (timestamp, user, action, module, record_id, details)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (timestamp, user, action, module, record_id, details),
        )
        conn.commit()
    except Exception as e:
        logger.error("Failed to write audit log: %s", e)


def get_audit_logs(
    limit: int = 200,
    offset: int = 0,
    search: str = "",
    action_filter: str = "",
    date_from: str = "",
    date_to: str = "",
) -> tuple[list[dict], int]:
    """
    Retrieve audit log entries with optional filtering.

    Returns (rows, total_count).
    """
    conn = get_connection()
    conditions = []
    params: list = []

    if search:
        conditions.append(
            "(user LIKE ? OR action LIKE ? OR module LIKE ? OR details LIKE ?)"
        )
        w = f"%{search}%"
        params.extend([w, w, w, w])

    if action_filter:
        conditions.append("action = ?")
        params.append(action_filter)

    if date_from:
        conditions.append("timestamp >= ?")
        params.append(date_from)

    if date_to:
        conditions.append("timestamp <= ?")
        params.append(date_to + " 23:59:59")

    where = " AND ".join(conditions) if conditions else "1=1"

    count_row = conn.execute(
        f"SELECT COUNT(*) as cnt FROM audit_logs WHERE {where}", params
    ).fetchone()
    total = count_row["cnt"] if count_row else 0

    rows = conn.execute(
        f"SELECT * FROM audit_logs WHERE {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        params + [limit, offset],
    ).fetchall()

    return [dict(r) for r in rows], total


def get_distinct_actions() -> list[str]:
    """Return the distinct action codes present in audit_logs."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT action FROM audit_logs ORDER BY action"
    ).fetchall()
    return [r["action"] for r in rows]
