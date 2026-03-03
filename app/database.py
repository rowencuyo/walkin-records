"""
SQLite database connection and schema management.
"""
import os
import sqlite3
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Resolve data directory relative to this file's parent (project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = _PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "walkin_records.db"
DOCUMENTS_DIR = DATA_DIR / "documents"
PROFILE_PICS_DIR = DATA_DIR / "profile_pictures"
LOGS_DIR = DATA_DIR / "logs"

_connection: sqlite3.Connection | None = None


def _ensure_dirs():
    """Create data directories if they don't exist."""
    for d in (DATA_DIR, DOCUMENTS_DIR, PROFILE_PICS_DIR, LOGS_DIR):
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
        _connection.execute("PRAGMA cache_size=-8000")  # 8 MB cache
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
    sex                     TEXT NOT NULL,
    date_of_birth           TEXT NOT NULL,
    passport_number         TEXT NOT NULL,
    country_of_citizenship  TEXT NOT NULL,
    -- Philippine Residential Address
    street                  TEXT DEFAULT '',
    barangay                TEXT DEFAULT '',
    city_municipality       TEXT DEFAULT '',
    province                TEXT DEFAULT '',
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
CREATE INDEX IF NOT EXISTS idx_documents_record ON documents(record_id);
CREATE INDEX IF NOT EXISTS idx_profile_pics_record ON profile_pictures(record_id);
"""


def initialize_database():
    """Create tables and indexes if they don't exist."""
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    logger.info("Database schema initialized")
