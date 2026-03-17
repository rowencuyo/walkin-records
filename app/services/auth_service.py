"""
Authentication service for single-user local login.
Passwords are hashed using PBKDF2-HMAC-SHA256 (stdlib only).
"""
import hashlib
import os
from datetime import datetime
from typing import Optional

from app.constants import PASSWORD_HASH_ITERATIONS
from app.database import get_connection
from app.utils.logger import get_logger
from core.audit_logger import log_action

logger = get_logger(__name__)


def _hash_password(password: str, salt: bytes) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS)
    return dk.hex()


class AuthService:
    """Single-user authentication backed by the auth table."""

    def is_setup_complete(self) -> bool:
        """Check if a password has been set (auth row exists)."""
        conn = get_connection()
        row = conn.execute("SELECT id FROM auth WHERE id = 1").fetchone()
        return row is not None

    def setup_password(self, username: str, password: str):
        """First-time password setup."""
        if self.is_setup_complete():
            raise ValueError("Password is already set up")

        salt = os.urandom(32)
        pw_hash = _hash_password(password, salt)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO auth (id, username, password_hash, salt,
                   username_changed_at, password_changed_at)
                   VALUES (1, ?, ?, ?, ?, ?)""",
                (username, pw_hash, salt.hex(), now, now),
            )
            conn.commit()
            logger.info("Initial password set for user '%s'", username)
        except Exception as e:
            conn.rollback()
            logger.error("Failed to setup password: %s", e)
            raise

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        """
        Verify credentials.
        Returns (success, error_message).
        """
        conn = get_connection()
        row = conn.execute(
            "SELECT username, password_hash, salt FROM auth WHERE id = 1"
        ).fetchone()
        if not row:
            return False, "No account configured"

        stored_username = row["username"]
        stored_hash = row["password_hash"]
        stored_salt = bytes.fromhex(row["salt"])

        if username != stored_username:
            self._record_failed_attempt()
            return False, "Incorrect username"

        computed = _hash_password(password, stored_salt)
        if computed != stored_hash:
            self._record_failed_attempt()
            return False, "Incorrect password"

        # Success — reset failed attempts
        self._reset_failed_attempts()
        log_action(username, "LOGIN", "auth", details="Login successful")
        return True, ""

    def authenticate_password_only(self, password: str) -> tuple[bool, str]:
        """Verify password only (for lock screen)."""
        conn = get_connection()
        row = conn.execute(
            "SELECT username, password_hash, salt FROM auth WHERE id = 1"
        ).fetchone()
        if not row:
            return False, "No account configured"

        stored_hash = row["password_hash"]
        stored_salt = bytes.fromhex(row["salt"])

        computed = _hash_password(password, stored_salt)
        if computed != stored_hash:
            self._record_failed_attempt()
            return False, "Incorrect password"

        self._reset_failed_attempts()
        return True, ""

    def get_username(self) -> str:
        """Get the stored username."""
        conn = get_connection()
        row = conn.execute("SELECT username FROM auth WHERE id = 1").fetchone()
        return row["username"] if row else "admin"

    def change_password(self, current_password: str, new_password: str) -> tuple[bool, str]:
        """Change password after verifying current one."""
        conn = get_connection()
        row = conn.execute(
            "SELECT password_hash, salt FROM auth WHERE id = 1"
        ).fetchone()
        if not row:
            return False, "No account configured"

        stored_hash = row["password_hash"]
        stored_salt = bytes.fromhex(row["salt"])
        computed = _hash_password(current_password, stored_salt)

        if computed != stored_hash:
            return False, "Current password is incorrect"

        new_salt = os.urandom(32)
        new_hash = _hash_password(new_password, new_salt)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            conn.execute(
                "UPDATE auth SET password_hash = ?, salt = ?, password_changed_at = ? WHERE id = 1",
                (new_hash, new_salt.hex(), now),
            )
            conn.commit()
            logger.info("Password changed")
            log_action("admin", "CHANGE_PASSWORD", "auth", details="Password changed")
            return True, ""
        except Exception as e:
            conn.rollback()
            logger.error("Failed to change password: %s", e)
            return False, str(e)

    def change_username(self, password: str, new_username: str) -> tuple[bool, str]:
        """Change username after verifying password."""
        ok, err = self.authenticate_password_only(password)
        if not ok:
            return False, err

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE auth SET username = ?, username_changed_at = ? WHERE id = 1",
                (new_username, now),
            )
            conn.commit()
            logger.info("Username changed to '%s'", new_username)
            log_action(new_username, "CHANGE_USERNAME", "auth",
                       details=f"Username changed to '{new_username}'")
            return True, ""
        except Exception as e:
            conn.rollback()
            return False, str(e)

    def get_metadata(self) -> dict:
        """Get auth metadata (change dates, failed attempts)."""
        conn = get_connection()
        row = conn.execute(
            """SELECT username, username_changed_at, password_changed_at,
               failed_attempts, last_failed_at FROM auth WHERE id = 1"""
        ).fetchone()
        if not row:
            return {}
        return dict(row)

    def _record_failed_attempt(self):
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE auth SET failed_attempts = failed_attempts + 1, last_failed_at = ? WHERE id = 1",
            (now,),
        )
        conn.commit()

    def _reset_failed_attempts(self):
        conn = get_connection()
        conn.execute(
            "UPDATE auth SET failed_attempts = 0 WHERE id = 1"
        )
        conn.commit()
