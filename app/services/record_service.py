"""
CRUD, search, filtering, and soft-delete operations for walk-in records.
"""
import sqlite3
from datetime import datetime
from typing import Optional

from app.database import get_connection
from app.models import WalkInRecord
from app.utils.logger import get_logger
from core.audit_logger import log_action

logger = get_logger(__name__)


class RecordService:
    """Service layer for WalkInRecord CRUD operations."""

    # --------------- CREATE ---------------
    def create_record(self, record: WalkInRecord) -> int:
        """Insert a new record. Returns the new record ID."""
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check duplicate active passport
        dup = self._check_duplicate_passport(record.passport_number, exclude_id=None)
        if dup:
            raise ValueError(
                f"An active record with passport '{record.passport_number}' already exists"
            )

        data = record.to_dict()
        data["created_at"] = now
        data["updated_at"] = now

        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO walkin_records ({cols}) VALUES ({placeholders})"

        try:
            cursor = conn.execute(sql, list(data.values()))
            conn.commit()
            record_id = cursor.lastrowid
            logger.info("Created record ID=%d, passport=%s", record_id, record.passport_number)
            log_action("admin", "CREATE_RECORD", "records", record_id,
                       f"Created record for {record.first_name} {record.last_name}")
            return record_id
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("Failed to create record: %s", e)
            raise

    # --------------- READ ---------------
    def get_record(self, record_id: int) -> Optional[WalkInRecord]:
        """Fetch a single record by ID."""
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM walkin_records WHERE id = ?", (record_id,)
        ).fetchone()
        if row:
            return WalkInRecord.from_row(dict(row))
        return None

    def get_all_records(
        self,
        include_inactive: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> list[WalkInRecord]:
        """Fetch records with pagination."""
        conn = get_connection()
        if include_inactive:
            sql = "SELECT * FROM walkin_records ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            rows = conn.execute(sql, (limit, offset)).fetchall()
        else:
            sql = "SELECT * FROM walkin_records WHERE is_active = 1 ORDER BY updated_at DESC LIMIT ? OFFSET ?"
            rows = conn.execute(sql, (limit, offset)).fetchall()
        return [WalkInRecord.from_row(dict(r)) for r in rows]

    def get_record_count(self, include_inactive: bool = False) -> int:
        """Get total record count for pagination."""
        conn = get_connection()
        if include_inactive:
            row = conn.execute("SELECT COUNT(*) as cnt FROM walkin_records").fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM walkin_records WHERE is_active = 1"
            ).fetchone()
        return row["cnt"] if row else 0

    def get_document_counts(self, record_ids: list[int]) -> dict[int, int]:
        """Get document counts for multiple records in one query."""
        if not record_ids:
            return {}
        conn = get_connection()
        placeholders = ",".join("?" * len(record_ids))
        sql = (
            f"SELECT record_id, COUNT(*) as cnt FROM documents "
            f"WHERE record_id IN ({placeholders}) GROUP BY record_id"
        )
        rows = conn.execute(sql, record_ids).fetchall()
        return {row["record_id"]: row["cnt"] for row in rows}

    def get_document_types(self, record_ids: list[int]) -> dict[int, list[str]]:
        """Get document types uploaded for multiple records in one query."""
        if not record_ids:
            return {}
        conn = get_connection()
        placeholders = ",".join("?" * len(record_ids))
        sql = (
            f"SELECT record_id, document_type FROM documents "
            f"WHERE record_id IN ({placeholders})"
        )
        rows = conn.execute(sql, record_ids).fetchall()
        result: dict[int, list[str]] = {}
        for row in rows:
            rid = row["record_id"]
            if rid not in result:
                result[rid] = []
            result[rid].append(row["document_type"])
        return result

    # --------------- SEARCH ---------------
    def search_records(
        self,
        query: str = "",
        visa_status: str = "",
        educational_level: str = "",
        year_level: str = "",
        active_status: str = "active",
        record_ids: list[int] | None = None,
        sort_column: str = "updated_at",
        sort_order: str = "DESC",
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[WalkInRecord], int]:
        """
        Search records with filters. Returns (records, total_count).
        """
        conn = get_connection()
        conditions = []
        params = []

        if active_status == "active":
            conditions.append("is_active = 1")
        elif active_status == "archived":
            conditions.append("is_active = 0")

        if record_ids is not None:
            if not record_ids:
                return [], 0  # Fast path: explicitly looking for specific IDs but list is empty
            placeholders = ",".join("?" for _ in record_ids)
            conditions.append(f"id IN ({placeholders})")
            params.extend(record_ids)

        if query:
            # Multi-word AND: each word must match at least one field
            searchable_fields = (
                "first_name", "last_name", "middle_name", "passport_number",
                "country_of_citizenship", "course_program", "visa_category",
                "visa_status", "educational_level", "year_level",
                "city_municipality", "province", "region", "remarks",
                "(first_name || ' ' || last_name)",
                "(first_name || ' ' || middle_name || ' ' || last_name)",
                "(last_name || ' ' || first_name)",
            )
            words = query.split()
            for word in words:
                w = f"%{word}%"
                word_conditions = " OR ".join(
                    f"{field} LIKE ?" for field in searchable_fields
                )
                conditions.append(f"({word_conditions})")
                params.extend([w] * len(searchable_fields))

        if visa_status:
            conditions.append("visa_status = ?")
            params.append(visa_status)

        if educational_level:
            conditions.append("educational_level = ?")
            params.append(educational_level)

        if year_level:
            conditions.append("year_level = ?")
            params.append(year_level)

        where = " AND ".join(conditions) if conditions else "1=1"

        # Validate sort column
        allowed_sorts = {
            "last_name", "first_name", "passport_number", "visa_status",
            "visa_category", "educational_level", "year_level",
            "course_program", "created_at", "updated_at",
        }
        if sort_column not in allowed_sorts:
            sort_column = "updated_at"
        sort_order = "ASC" if sort_order.upper() == "ASC" else "DESC"

        # Count
        count_sql = f"SELECT COUNT(*) as cnt FROM walkin_records WHERE {where}"
        count_row = conn.execute(count_sql, params).fetchone()
        total = count_row["cnt"] if count_row else 0

        # Fetch
        fetch_sql = (
            f"SELECT * FROM walkin_records WHERE {where} "
            f"ORDER BY {sort_column} {sort_order} LIMIT ? OFFSET ?"
        )
        rows = conn.execute(fetch_sql, params + [limit, offset]).fetchall()
        records = [WalkInRecord.from_row(dict(r)) for r in rows]

        return records, total

    # --------------- UPDATE ---------------
    def update_record(self, record_id: int, record: WalkInRecord) -> bool:
        """Update an existing record."""
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check duplicate passport (exclude self)
        dup = self._check_duplicate_passport(record.passport_number, exclude_id=record_id)
        if dup:
            raise ValueError(
                f"An active record with passport '{record.passport_number}' already exists"
            )

        data = record.to_dict()
        data["updated_at"] = now
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        sql = f"UPDATE walkin_records SET {set_clause} WHERE id = ?"

        try:
            cursor = conn.execute(sql, list(data.values()) + [record_id])
            conn.commit()
            if cursor.rowcount > 0:
                logger.info("Updated record ID=%d", record_id)
                log_action("admin", "EDIT_RECORD", "records", record_id,
                           f"Updated record for {record.first_name} {record.last_name}")
                return True
            return False
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("Failed to update record ID=%d: %s", record_id, e)
            raise

    # --------------- SOFT DELETE / RESTORE ---------------
    def soft_delete(self, record_id: int) -> bool:
        """Mark a record as inactive."""
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor = conn.execute(
                "UPDATE walkin_records SET is_active = 0, updated_at = ? WHERE id = ?",
                (now, record_id),
            )
            conn.commit()
            if cursor.rowcount > 0:
                logger.info("Soft-deleted record ID=%d", record_id)
                log_action("admin", "DELETE_RECORD", "records", record_id,
                           "Record deactivated (soft-delete)")
                return True
            return False
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("Failed to soft-delete record ID=%d: %s", record_id, e)
            raise

    def restore(self, record_id: int) -> bool:
        """Restore a soft-deleted record."""
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if restoring would create a duplicate passport
        rec = self.get_record(record_id)
        if rec:
            dup = self._check_duplicate_passport(rec.passport_number, exclude_id=record_id)
            if dup:
                raise ValueError(
                    f"Cannot restore: an active record with passport '{rec.passport_number}' already exists"
                )

        try:
            cursor = conn.execute(
                "UPDATE walkin_records SET is_active = 1, updated_at = ? WHERE id = ?",
                (now, record_id),
            )
            conn.commit()
            if cursor.rowcount > 0:
                logger.info("Restored record ID=%d", record_id)
                log_action("admin", "RESTORE_RECORD", "records", record_id,
                           "Record restored from inactive")
                return True
            return False
        except sqlite3.Error as e:
            conn.rollback()
            logger.error("Failed to restore record ID=%d: %s", record_id, e)
            raise

    # --------------- HELPERS ---------------
    def _check_duplicate_passport(
        self, passport_number: str, exclude_id: Optional[int]
    ) -> bool:
        """Check if an active record already has this passport number."""
        conn = get_connection()
        if exclude_id is not None:
            row = conn.execute(
                "SELECT id FROM walkin_records WHERE passport_number = ? AND is_active = 1 AND id != ?",
                (passport_number, exclude_id),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM walkin_records WHERE passport_number = ? AND is_active = 1",
                (passport_number,),
            ).fetchone()
        return row is not None
