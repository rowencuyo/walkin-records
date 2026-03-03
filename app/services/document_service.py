"""
Document file management service.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.database import get_connection, DOCUMENTS_DIR
from app.models import Document
from app.constants import ALLOWED_DOCUMENT_EXTENSIONS, MAX_DOCUMENT_SIZE_BYTES
from app.utils.logger import get_logger
from app.utils.validators import validate_file_type, validate_file_size

logger = get_logger(__name__)


class DocumentService:
    """Handles document file storage and database registration."""

    def save_document(
        self, record_id: int, document_type: str, source_path: str
    ) -> Document:
        """Copy a document file to storage and register it in the database."""
        # Validate
        err = validate_file_type(source_path, ALLOWED_DOCUMENT_EXTENSIONS)
        if err:
            raise ValueError(err)
        err = validate_file_size(source_path, MAX_DOCUMENT_SIZE_BYTES)
        if err:
            raise ValueError(err)

        src = Path(source_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create record-specific directory
        rec_dir = DOCUMENTS_DIR / str(record_id)
        rec_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_name = f"{document_type.replace(' ', '_')}_{timestamp}{src.suffix}"
        dest_path = rec_dir / dest_name

        # Copy file
        shutil.copy2(str(src), str(dest_path))

        # Register in database
        conn = get_connection()
        try:
            cursor = conn.execute(
                """INSERT INTO documents 
                   (record_id, document_type, file_path, file_name, file_type, file_size, upload_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    record_id,
                    document_type,
                    str(dest_path),
                    src.name,
                    src.suffix.lower(),
                    src.stat().st_size,
                    now,
                ),
            )
            conn.commit()
            doc = Document(
                id=cursor.lastrowid,
                record_id=record_id,
                document_type=document_type,
                file_path=str(dest_path),
                file_name=src.name,
                file_type=src.suffix.lower(),
                file_size=src.stat().st_size,
                upload_date=now,
            )
            logger.info("Saved document ID=%d for record %d", doc.id, record_id)
            return doc
        except Exception as e:
            conn.rollback()
            # Cleanup copied file on failure
            if dest_path.exists():
                dest_path.unlink()
            logger.error("Failed to save document: %s", e)
            raise

    def get_documents(self, record_id: int) -> list[Document]:
        """Get all documents for a record."""
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM documents WHERE record_id = ? ORDER BY upload_date DESC",
            (record_id,),
        ).fetchall()
        return [Document.from_row(dict(r)) for r in rows]

    def delete_document(self, doc_id: int) -> bool:
        """Delete a document file and its database entry."""
        conn = get_connection()
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            return False

        doc = Document.from_row(dict(row))

        # Remove file
        try:
            p = Path(doc.file_path)
            if p.exists():
                p.unlink()
        except OSError as e:
            logger.warning("Could not delete file %s: %s", doc.file_path, e)

        # Remove DB entry
        try:
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            logger.info("Deleted document ID=%d", doc_id)
            return True
        except Exception as e:
            conn.rollback()
            logger.error("Failed to delete document ID=%d: %s", doc_id, e)
            raise

    def get_document(self, doc_id: int) -> Optional[Document]:
        """Get a single document by ID."""
        conn = get_connection()
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if row:
            return Document.from_row(dict(row))
        return None
