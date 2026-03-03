"""
Profile picture management with automatic compression.
"""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject
from PySide6.QtGui import QImage

from app.database import get_connection, PROFILE_PICS_DIR
from app.models import ProfilePicture
from app.constants import ALLOWED_IMAGE_EXTENSIONS, MAX_PROFILE_PIC_SIZE_BYTES
from app.utils.logger import get_logger
from app.utils.validators import validate_file_type

logger = get_logger(__name__)


class _CompressSignals(QObject):
    finished = Signal(str)  # final path
    error = Signal(str)     # error message


class _CompressTask(QRunnable):
    """Background task to compress an image if it exceeds size limit."""

    def __init__(self, source_path: str, dest_path: str, max_bytes: int):
        super().__init__()
        self.source = source_path
        self.dest = dest_path
        self.max_bytes = max_bytes
        self.signals = _CompressSignals()

    def run(self):
        try:
            src = Path(self.source)
            size = src.stat().st_size

            if size <= self.max_bytes:
                # No compression needed, just copy
                shutil.copy2(self.source, self.dest)
                self.signals.finished.emit(self.dest)
                return

            # Load and compress
            img = QImage(self.source)
            if img.isNull():
                self.signals.error.emit("Failed to load image file")
                return

            # Try progressively lower quality
            quality = 85
            while quality >= 10:
                img.save(self.dest, quality=quality)
                if Path(self.dest).stat().st_size <= self.max_bytes:
                    self.signals.finished.emit(self.dest)
                    return
                quality -= 10

            # Try scaling down
            for scale in [0.75, 0.5, 0.25]:
                scaled = img.scaled(
                    int(img.width() * scale),
                    int(img.height() * scale),
                )
                scaled.save(self.dest, quality=60)
                if Path(self.dest).stat().st_size <= self.max_bytes:
                    self.signals.finished.emit(self.dest)
                    return

            self.signals.error.emit(
                "Cannot compress image below 5 MB limit. Please use a smaller image."
            )
        except Exception as e:
            self.signals.error.emit(str(e))


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
        Runs compression in a background thread.
        on_success(path: str), on_error(msg: str) are optional callbacks.
        """
        err = validate_file_type(source_path, ALLOWED_IMAGE_EXTENSIONS)
        if err:
            if on_error:
                on_error(err)
            return

        # Prepare destination
        rec_dir = PROFILE_PICS_DIR / str(record_id)
        rec_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(source_path).suffix.lower()
        if ext == ".webp":
            ext = ".png"  # Convert WebP to PNG for broader compatibility
        dest_path = str(rec_dir / f"profile{ext}")

        # Remove old picture first
        self._remove_old_files(record_id)

        task = _CompressTask(source_path, dest_path, MAX_PROFILE_PIC_SIZE_BYTES)

        def _on_finished(final_path):
            self._register_in_db(record_id, final_path)
            if on_success:
                on_success(final_path)

        def _on_error(msg):
            logger.error("Profile picture compression failed: %s", msg)
            if on_error:
                on_error(msg)

        task.signals.finished.connect(_on_finished)
        task.signals.error.connect(_on_error)

        QThreadPool.globalInstance().start(task)

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
