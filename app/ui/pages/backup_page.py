"""
Backup / Restore page with timestamp tracking.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout,
)

from app.database import DATA_DIR, DB_PATH, close_connection, initialize_database
from app.utils.logger import get_logger

logger = get_logger(__name__)

BACKUP_META_FILE = DATA_DIR / "backup_meta.json"


class BackupPage(QWidget):
    """Manual backup and restore page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(16)

        title = QLabel("Backup & Restore")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Create a backup of your database and files, or restore from a previous backup."
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # Backup section
        backup_group = QGroupBox("Backup")
        backup_layout = QVBoxLayout()
        backup_layout.setSpacing(12)
        backup_layout.setContentsMargins(12, 16, 12, 12)

        backup_desc = QLabel(
            "Export the database and all associated files (documents, profile pictures) "
            "to a folder of your choice."
        )
        backup_desc.setWordWrap(True)
        backup_desc.setObjectName("subtitleLabel")
        backup_layout.addWidget(backup_desc)

        info_layout = QFormLayout()
        info_layout.setSpacing(6)

        self._db_size_label = QLabel(self._get_db_size())
        info_layout.addRow(QLabel("Database size:"), self._db_size_label)

        self._data_dir_label = QLabel(str(DATA_DIR))
        self._data_dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addRow(QLabel("Data directory:"), self._data_dir_label)

        self._last_backup_label = QLabel(self._get_last_backup_text())
        info_layout.addRow(QLabel("Last backup:"), self._last_backup_label)

        backup_layout.addLayout(info_layout)

        backup_btn = QPushButton("Create Backup")
        backup_btn.setObjectName("primaryButton")
        backup_btn.setFixedHeight(36)
        backup_btn.setFixedWidth(200)
        backup_btn.clicked.connect(self._on_backup)
        backup_layout.addWidget(backup_btn)

        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)

        # Restore section
        restore_group = QGroupBox("Restore")
        restore_layout = QVBoxLayout()
        restore_layout.setSpacing(12)
        restore_layout.setContentsMargins(12, 16, 12, 12)

        restore_desc = QLabel(
            "Restore data from a previous backup folder. This will replace all current data."
        )
        restore_desc.setWordWrap(True)
        restore_desc.setObjectName("subtitleLabel")
        restore_layout.addWidget(restore_desc)

        warning = QLabel(
            "Warning: Restoring will overwrite your current database and files. "
            "Create a backup first if you have important data."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #FF9500; font-weight: 500;")
        restore_layout.addWidget(warning)

        restore_btn = QPushButton("Restore from Backup")
        restore_btn.setObjectName("dangerButton")
        restore_btn.setFixedHeight(36)
        restore_btn.setFixedWidth(200)
        restore_btn.clicked.connect(self._on_restore)
        restore_layout.addWidget(restore_btn)

        restore_group.setLayout(restore_layout)
        layout.addWidget(restore_group)

        layout.addStretch()

    def _get_db_size(self) -> str:
        if DB_PATH.exists():
            size = DB_PATH.stat().st_size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "No database"

    def _on_backup(self):
        dest_dir = QFileDialog.getExistingDirectory(
            self, "Select Backup Destination"
        )
        if not dest_dir:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(dest_dir) / f"archivium_backup_{timestamp}"

        try:
            # Copy entire data directory
            shutil.copytree(str(DATA_DIR), str(backup_dir))
            self._db_size_label.setText(self._get_db_size())
            self._save_backup_timestamp()
            self._last_backup_label.setText(self._get_last_backup_text())
            QMessageBox.information(
                self, "Backup Complete",
                f"Backup saved to:\n{backup_dir}"
            )
            logger.info("Backup created at %s", backup_dir)
        except Exception as e:
            logger.error("Backup failed: %s", e)
            QMessageBox.critical(self, "Backup Failed", f"Error: {e}")

    def _on_restore(self):
        reply = QMessageBox.warning(
            self, "Confirm Restore",
            "This will REPLACE all current data with the backup.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        src_dir = QFileDialog.getExistingDirectory(
            self, "Select Backup Folder to Restore"
        )
        if not src_dir:
            return

        src = Path(src_dir)
        # Validate backup
        if not (src / "walkin_records.db").exists():
            QMessageBox.warning(
                self, "Invalid Backup",
                "The selected folder does not contain a valid backup (missing walkin_records.db)."
            )
            return

        try:
            close_connection()

            # Remove current data and replace with backup
            if DATA_DIR.exists():
                shutil.rmtree(str(DATA_DIR))
            shutil.copytree(str(src), str(DATA_DIR))

            initialize_database()
            self._db_size_label.setText(self._get_db_size())

            QMessageBox.information(
                self, "Restore Complete",
                "Data has been restored from backup.\n"
                "The application will use the restored data."
            )
            logger.info("Restored from backup at %s", src)
        except Exception as e:
            logger.error("Restore failed: %s", e)
            QMessageBox.critical(self, "Restore Failed", f"Error: {e}")

    def _save_backup_timestamp(self):
        """Record the current time as the last backup timestamp."""
        try:
            with open(BACKUP_META_FILE, "w") as f:
                json.dump({"last_backup": datetime.now().isoformat()}, f)
        except Exception as e:
            logger.warning("Failed to save backup timestamp: %s", e)

    def _get_last_backup_text(self) -> str:
        """Get a human-readable last backup string."""
        try:
            if BACKUP_META_FILE.exists():
                with open(BACKUP_META_FILE, "r") as f:
                    meta = json.load(f)
                ts = datetime.fromisoformat(meta.get("last_backup", ""))
                days_ago = (datetime.now() - ts).days
                if days_ago == 0:
                    return f"Today ({ts.strftime('%H:%M')})"
                elif days_ago == 1:
                    return f"Yesterday ({ts.strftime('%Y-%m-%d')})"
                else:
                    return f"{days_ago} days ago ({ts.strftime('%Y-%m-%d')})"
        except Exception:
            pass
        return "Never"
