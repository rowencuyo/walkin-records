"""
SQLite database connection and schema management.
"""
import os
import sqlite3
from pathlib import Path

from app.constants import DATABASE_CACHE_SIZE_KB
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Resolve data directory relative to this file's parent (project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "walkin_records.db"
DOCUMENTS_DIR = DATA_DIR / "documents"
PROFILE_PICS_DIR = DATA_DIR / "profile_pictures"
LOGS_DIR = DATA_DIR / "logs"
DRAFTS_DIR = DATA_DIR / "drafts"

_connection: sqlite3.Connection | None = None


def _ensure_dirs():
    """Create data directories if they don't exist."""
    for d in (DATA_DIR, DOCUMENTS_DIR, PROFILE_PICS_DIR, LOGS_DIR, DRAFTS_DIR):
        d.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Return the singleton database connection."""
    global _connection
    if _connection is None:
        _ensure_dirs()
        _connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        # Performance pragmas
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA synchronous=NORMAL")
        _connection.execute("PRAGMA foreign_keys=ON")
        _connection.execute(f"PRAGMA cache_size=-{DATABASE_CACHE_SIZE_KB}")
        logger.info("Database connection established at %s", DB_PATH)
    return _connection


def close_connection():
    """Close the database connection."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        logger.info("Database connection closed")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS walkin_records (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Identity
    last_name               TEXT NOT NULL,
    first_name              TEXT NOT NULL,
    middle_name             TEXT DEFAULT '',
    suffix_name             TEXT DEFAULT '',
    sex                     TEXT NOT NULL,
    date_of_birth           TEXT NOT NULL,
    passport_number         TEXT NOT NULL,
    country_of_citizenship  TEXT NOT NULL,
    -- Philippine Residential Address
    street                  TEXT DEFAULT '',
    barangay                TEXT DEFAULT '',
    city_municipality       TEXT DEFAULT '',
    province                TEXT DEFAULT '',
    region                  TEXT DEFAULT '',
    -- Academic & Residency
    date_of_arrival         TEXT DEFAULT '',
    date_start_education    TEXT DEFAULT '',
    educational_level       TEXT DEFAULT '',
    course_program          TEXT DEFAULT '',
    year_level              TEXT DEFAULT '',
    semester                TEXT DEFAULT '',
    -- Visa
    visa_category           TEXT DEFAULT '',
    visa_grant_date         TEXT DEFAULT '',
    visa_validity_date      TEXT DEFAULT '',
    visa_status             TEXT DEFAULT '',
    remarks                 TEXT DEFAULT '',
    -- Enrollment
    location_status         TEXT DEFAULT '',
    enrollment_status       TEXT DEFAULT '',
    -- System
    is_active               INTEGER DEFAULT 1,
    created_at              TEXT NOT NULL,
    updated_at              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id       INTEGER NOT NULL,
    document_type   TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    file_type       TEXT NOT NULL,
    file_size       INTEGER DEFAULT 0,
    upload_date     TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES walkin_records(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS profile_pictures (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id   INTEGER NOT NULL UNIQUE,
    file_path   TEXT NOT NULL,
    upload_date TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES walkin_records(id) ON DELETE CASCADE
);

-- Indexes for fast searching
CREATE INDEX IF NOT EXISTS idx_records_passport ON walkin_records(passport_number);
CREATE INDEX IF NOT EXISTS idx_records_last_name ON walkin_records(last_name);
CREATE INDEX IF NOT EXISTS idx_records_first_name ON walkin_records(first_name);
CREATE INDEX IF NOT EXISTS idx_records_visa_status ON walkin_records(visa_status);
CREATE INDEX IF NOT EXISTS idx_records_is_active ON walkin_records(is_active);
CREATE INDEX IF NOT EXISTS idx_records_active_passport
    ON walkin_records(passport_number, is_active);
CREATE INDEX IF NOT EXISTS idx_records_visa_validity
    ON walkin_records(visa_validity_date, is_active);
CREATE INDEX IF NOT EXISTS idx_documents_record ON documents(record_id);
CREATE INDEX IF NOT EXISTS idx_profile_pics_record ON profile_pictures(record_id);

-- v1.2: Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    severity        TEXT NOT NULL,
    category        TEXT NOT NULL,
    title           TEXT NOT NULL,
    message         TEXT NOT NULL,
    group_key       TEXT DEFAULT '',
    record_id       INTEGER,
    status          TEXT DEFAULT 'unread',
    created_at      TEXT NOT NULL,
    resolved_at     TEXT DEFAULT '',
    FOREIGN KEY (record_id) REFERENCES walkin_records(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_group ON notifications(group_key);

-- v1.2: Authentication (single-user, single-row enforced)
CREATE TABLE IF NOT EXISTS auth (
    id                  INTEGER PRIMARY KEY CHECK (id = 1),
    username            TEXT NOT NULL DEFAULT 'admin',
    password_hash       TEXT NOT NULL,
    salt                TEXT NOT NULL,
    username_changed_at TEXT DEFAULT '',
    password_changed_at TEXT DEFAULT '',
    failed_attempts     INTEGER DEFAULT 0,
    last_failed_at      TEXT DEFAULT ''
);

-- v1.2: Preferences (key-value store)
CREATE TABLE IF NOT EXISTS preferences (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

-- v1.2: Recent activity tracking
CREATE TABLE IF NOT EXISTS recent_activity (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id   INTEGER NOT NULL,
    action      TEXT NOT NULL,
    timestamp   TEXT NOT NULL,
    FOREIGN KEY (record_id) REFERENCES walkin_records(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_recent_activity_ts ON recent_activity(timestamp DESC);

-- v1.5: Audit logging
CREATE TABLE IF NOT EXISTS audit_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT NOT NULL,
    user        TEXT NOT NULL,
    action      TEXT NOT NULL,
    module      TEXT NOT NULL,
    record_id   INTEGER,
    details     TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_ts ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
"""


def initialize_database():
    """Create tables and indexes if they don't exist, and migrate existing DBs."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)

    # v1.5 migration: add new columns to existing databases
    _migrate_add_column(conn, "walkin_records", "suffix_name", "TEXT DEFAULT ''")
    _migrate_add_column(conn, "walkin_records", "region", "TEXT DEFAULT ''")
    _migrate_add_column(conn, "walkin_records", "location_status", "TEXT DEFAULT ''")
    _migrate_add_column(conn, "walkin_records", "enrollment_status", "TEXT DEFAULT ''")

    conn.commit()
    logger.info("Database schema initialized")


def _migrate_add_column(conn, table: str, column: str, definition: str):
    """Safely add a column if it doesn't already exist (SQLite migration helper)."""
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        logger.info("Migrated: added column '%s' to '%s'", column, table)
