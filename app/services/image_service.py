"""
Profile picture management with automatic compression.
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QImage

from app.database import get_connection, PROFILE_PICS_DIR
from app.models import ProfilePicture
from app.constants import ALLOWED_IMAGE_EXTENSIONS, MAX_PROFILE_PIC_SIZE_BYTES
from app.utils.logger import get_logger
from app.utils.validators import validate_file_type

logger = get_logger(__name__)




class ImageService:
    """Manages profile picture storage and compression."""

    def save_profile_picture(
        self,
        record_id: int,
        source_path: str,
        on_success=None,
        on_error=None,
    ):
        """
        Save a profile picture, compressing if needed.
        Executes synchronously to avoid SQLite threading issues.
        """
        try:
            final_path = self.save_profile_picture_sync(record_id, source_path)
            if on_success:
                on_success(final_path)
        except Exception as e:
            logger.error("Profile picture compression failed: %s", e)
            if on_error:
                on_error(str(e))

    def save_profile_picture_sync(self, record_id: int, source_path: str) -> str:
        """
        Synchronous version for non-UI contexts.
        Returns the final path or raises an error.
        """
        err = validate_file_type(source_path, ALLOWED_IMAGE_EXTENSIONS)
        if err:
            raise ValueError(err)

        rec_dir = PROFILE_PICS_DIR / str(record_id)
        rec_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(source_path).suffix.lower()
        dest_path = str(rec_dir / f"profile{ext}")

        self._remove_old_files(record_id)

        src = Path(source_path)
        if src.stat().st_size <= MAX_PROFILE_PIC_SIZE_BYTES:
            shutil.copy2(source_path, dest_path)
        else:
            img = QImage(source_path)
            if img.isNull():
                raise ValueError("Failed to load image")
            quality = 85
            saved = False
            while quality >= 10:
                img.save(dest_path, quality=quality)
                if Path(dest_path).stat().st_size <= MAX_PROFILE_PIC_SIZE_BYTES:
                    saved = True
                    break
                quality -= 10
            if not saved:
                raise ValueError("Cannot compress image below 5 MB limit")

        self._register_in_db(record_id, dest_path)
        return dest_path

    def get_profile_picture_path(self, record_id: int) -> Optional[str]:
        """Get the profile picture path for a record, or None."""
        conn = get_connection()
        row = conn.execute(
            "SELECT file_path FROM profile_pictures WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        if row:
            p = Path(row["file_path"])
            if p.exists():
                return str(p)
        return None

    def delete_profile_picture(self, record_id: int) -> bool:
        """Delete profile picture file and DB entry."""
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM profile_pictures WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        if not row:
            return False

        # Remove file
        try:
            p = Path(row["file_path"])
            if p.exists():
                p.unlink()
        except OSError as e:
            logger.warning("Could not delete profile pic: %s", e)

        conn.execute("DELETE FROM profile_pictures WHERE record_id = ?", (record_id,))
        conn.commit()
        logger.info("Deleted profile picture for record %d", record_id)
        return True

    def _remove_old_files(self, record_id: int):
        """Remove existing profile picture files."""
        conn = get_connection()
        row = conn.execute(
            "SELECT file_path FROM profile_pictures WHERE record_id = ?",
            (record_id,),
        ).fetchone()
        if row:
            try:
                p = Path(row["file_path"])
                if p.exists():
                    p.unlink()
            except OSError:
                pass
            conn.execute("DELETE FROM profile_pictures WHERE record_id = ?", (record_id,))
            conn.commit()

    def _register_in_db(self, record_id: int, file_path: str):
        """Register profile picture in database."""
        conn = get_connection()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn.execute(
                """INSERT OR REPLACE INTO profile_pictures 
                   (record_id, file_path, upload_date) VALUES (?, ?, ?)""",
                (record_id, file_path, now),
            )
            conn.commit()
            logger.info("Registered profile picture for record %d", record_id)
        except Exception as e:
            conn.rollback()
            logger.error("Failed to register profile picture: %s", e)
            raise
