"""
Key-value preferences service backed by the preferences table.
All values are stored as strings. Applied immediately.
"""
from app.database import get_connection
from app.constants import DEFAULT_PREFERENCES
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PreferencesService:
    """Local key-value preferences store."""

    def get(self, key: str, default: str | None = None) -> str:
        """Get a preference value. Falls back to DEFAULT_PREFERENCES, then to default."""
        conn = get_connection()
        row = conn.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        ).fetchone()
        if row:
            return row["value"]
        return DEFAULT_PREFERENCES.get(key, default or "")

    def get_bool(self, key: str) -> bool:
        """Get a boolean preference (stored as 'true'/'false')."""
        return self.get(key, "false").lower() == "true"

    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer preference."""
        try:
            return int(self.get(key, str(default)))
        except ValueError:
            return default

    def set(self, key: str, value: str):
        """Set a preference. Creates or updates."""
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Failed to set preference '%s': %s", key, e)

    def set_bool(self, key: str, value: bool):
        """Set a boolean preference."""
        self.set(key, "true" if value else "false")

    def set_int(self, key: str, value: int):
        """Set an integer preference."""
        self.set(key, str(value))

    def get_all(self) -> dict[str, str]:
        """Get all preferences, merged with defaults."""
        result = dict(DEFAULT_PREFERENCES)
        conn = get_connection()
        rows = conn.execute("SELECT key, value FROM preferences").fetchall()
        for row in rows:
            result[row["key"]] = row["value"]
        return result
