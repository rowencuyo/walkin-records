"""Settings page — security, notification preferences, backup, and about."""
import json
import shutil
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGroupBox, QFormLayout,
    QCheckBox, QComboBox, QSpinBox, QLineEdit, QMessageBox,
    QFileDialog,
)

from app.database import DATA_DIR, DB_PATH, close_connection, initialize_database
from app.services.auth_service import AuthService
from app.services.preferences_service import PreferencesService
from app.constants import AUTO_LOCK_TIMEOUT_OPTIONS
from app.ui.theme import Colors
from app.utils.logger import get_logger

logger = get_logger(__name__)

BACKUP_META_FILE = DATA_DIR / "backup_meta.json"


class SettingsPage(QWidget):
    """Application settings: security, notifications, about."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth = AuthService()
        self._prefs = PreferencesService()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(0, 0, 12, 0)

        content_layout.addWidget(self._create_security_section())
        content_layout.addWidget(self._create_notification_section())
        content_layout.addWidget(self._create_backup_section())
        content_layout.addWidget(self._create_about_section())
        content_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

    # ── Security ──

    def _create_security_section(self) -> QGroupBox:
        group = QGroupBox("Security")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 20, 16, 16)

        # Idle auto-lock
        lock_row = QHBoxLayout()
        self._idle_lock_cb = QCheckBox("Enable idle auto-lock")
        self._idle_lock_cb.setChecked(self._prefs.get_bool("idle_lock_enabled"))
        self._idle_lock_cb.stateChanged.connect(self._on_idle_lock_changed)
        lock_row.addWidget(self._idle_lock_cb)

        self._timeout_combo = QComboBox()
        for minutes in AUTO_LOCK_TIMEOUT_OPTIONS:
            self._timeout_combo.addItem(f"{minutes} min", minutes)
        current_timeout = self._prefs.get_int("idle_lock_timeout_min", 15)
        idx = self._timeout_combo.findData(current_timeout)
        if idx >= 0:
            self._timeout_combo.setCurrentIndex(idx)
        self._timeout_combo.setEnabled(self._idle_lock_cb.isChecked())
        self._timeout_combo.currentIndexChanged.connect(self._on_timeout_changed)
        lock_row.addWidget(self._timeout_combo)
        lock_row.addStretch()
        layout.addLayout(lock_row)

        # Credential metadata
        meta = self._auth.get_metadata()
        if meta:
            info_layout = QFormLayout()
            info_layout.setSpacing(6)
            info_layout.addRow(
                QLabel("Username:"),
                QLabel(meta.get("username", "admin")),
            )
            info_layout.addRow(
                QLabel("Password last changed:"),
                QLabel(meta.get("password_changed_at", "Never")[:16]),
            )
            info_layout.addRow(
                QLabel("Username last changed:"),
                QLabel(meta.get("username_changed_at", "Never")[:16]),
            )
            failed = meta.get("failed_attempts", 0)
            if failed:
                info_layout.addRow(
                    QLabel("Failed login attempts:"),
                    QLabel(str(failed)),
                )
            layout.addLayout(info_layout)

        # Change password
        btn_row = QHBoxLayout()
        change_pw_btn = QPushButton("Change Password")
        change_pw_btn.setFixedHeight(34)
        change_pw_btn.clicked.connect(self._on_change_password)
        btn_row.addWidget(change_pw_btn)

        change_user_btn = QPushButton("Change Username")
        change_user_btn.setFixedHeight(34)
        change_user_btn.clicked.connect(self._on_change_username)
        btn_row.addWidget(change_user_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        group.setLayout(layout)
        return group

    # ── Notifications ──

    def _create_notification_section(self) -> QGroupBox:
        group = QGroupBox("Notifications")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 20, 16, 16)

        # Visa expiry toggle
        self._visa_cb = QCheckBox("Visa expiry & expiring notifications")
        self._visa_cb.setChecked(self._prefs.get_bool("notify_visa_expiry"))
        self._visa_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("notify_visa_expiry", self._visa_cb.isChecked())
        )
        layout.addWidget(self._visa_cb)

        # Threshold
        threshold_row = QHBoxLayout()
        threshold_row.addWidget(QLabel("Warn before visa expires:"))
        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(7, 180)
        self._threshold_spin.setSuffix(" days")
        self._threshold_spin.setValue(self._prefs.get_int("visa_expiry_threshold_days", 30))
        self._threshold_spin.valueChanged.connect(
            lambda v: self._prefs.set_int("visa_expiry_threshold_days", v)
        )
        threshold_row.addWidget(self._threshold_spin)
        threshold_row.addStretch()
        layout.addLayout(threshold_row)

        # Missing docs toggle
        self._docs_cb = QCheckBox("Missing documents notifications")
        self._docs_cb.setChecked(self._prefs.get_bool("notify_missing_docs"))
        self._docs_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("notify_missing_docs", self._docs_cb.isChecked())
        )
        layout.addWidget(self._docs_cb)

        # Backup reminder toggle
        self._backup_cb = QCheckBox("Backup reminders")
        self._backup_cb.setChecked(self._prefs.get_bool("notify_backup_reminder"))
        self._backup_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("notify_backup_reminder", self._backup_cb.isChecked())
        )
        layout.addWidget(self._backup_cb)

        # Retention
        retention_row = QHBoxLayout()
        retention_row.addWidget(QLabel("Notification history retention:"))
        self._retention_spin = QSpinBox()
        self._retention_spin.setRange(7, 365)
        self._retention_spin.setSuffix(" days")
        self._retention_spin.setValue(self._prefs.get_int("notification_retention_days", 90))
        self._retention_spin.valueChanged.connect(
            lambda v: self._prefs.set_int("notification_retention_days", v)
        )
        retention_row.addWidget(self._retention_spin)
        retention_row.addStretch()
        layout.addLayout(retention_row)

        group.setLayout(layout)
        return group

    # ── Backup & Restore ──

    def _create_backup_section(self) -> QGroupBox:
        group = QGroupBox("Backup & Restore")
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 20, 16, 16)

        desc = QLabel(
            "Export or restore the database and all associated files "
            "(documents, profile pictures)."
        )
        desc.setWordWrap(True)
        desc.setObjectName("subtitleLabel")
        layout.addWidget(desc)

        info_layout = QFormLayout()
        info_layout.setSpacing(6)

        self._db_size_label = QLabel(self._get_db_size())
        info_layout.addRow(QLabel("Database size:"), self._db_size_label)

        dir_label = QLabel(str(DATA_DIR))
        dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addRow(QLabel("Data directory:"), dir_label)

        self._last_backup_label = QLabel(self._get_last_backup_text())
        info_layout.addRow(QLabel("Last backup:"), self._last_backup_label)

        layout.addLayout(info_layout)

        btn_row = QHBoxLayout()
        backup_btn = QPushButton("Create Backup")
        backup_btn.setObjectName("primaryButton")
        backup_btn.setFixedHeight(36)
        backup_btn.clicked.connect(self._on_backup)
        btn_row.addWidget(backup_btn)

        restore_btn = QPushButton("Restore from Backup")
        restore_btn.setObjectName("dangerButton")
        restore_btn.setFixedHeight(36)
        restore_btn.clicked.connect(self._on_restore)
        btn_row.addWidget(restore_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        warning = QLabel(
            "Warning: Restoring will overwrite all current data. "
            "Create a backup first."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #FF9500; font-size: 12px;")
        layout.addWidget(warning)

        group.setLayout(layout)
        return group

    # ── About ──

    def _create_about_section(self) -> QGroupBox:
        group = QGroupBox("About")
        layout = QFormLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(16, 20, 16, 16)

        layout.addRow(QLabel("Application:"), QLabel("Archivium"))
        layout.addRow(QLabel("Version:"), QLabel("1.2"))

        data_label = QLabel(str(DATA_DIR))
        data_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addRow(QLabel("Data directory:"), data_label)

        group.setLayout(layout)
        return group

    # ── Actions ──

    def _on_idle_lock_changed(self):
        enabled = self._idle_lock_cb.isChecked()
        self._prefs.set_bool("idle_lock_enabled", enabled)
        self._timeout_combo.setEnabled(enabled)

    def _on_timeout_changed(self):
        minutes = self._timeout_combo.currentData()
        if minutes:
            self._prefs.set_int("idle_lock_timeout_min", minutes)

    def _on_change_password(self):
        from PySide6.QtWidgets import QInputDialog

        current, ok = QInputDialog.getText(
            self, "Change Password", "Current password:", QLineEdit.Password
        )
        if not ok or not current:
            return

        new_pw, ok = QInputDialog.getText(
            self, "Change Password", "New password:", QLineEdit.Password
        )
        if not ok or not new_pw:
            return

        confirm, ok = QInputDialog.getText(
            self, "Change Password", "Confirm new password:", QLineEdit.Password
        )
        if not ok:
            return

        if new_pw != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        if len(new_pw) < 4:
            QMessageBox.warning(self, "Error", "Password must be at least 4 characters")
            return

        success, err = self._auth.change_password(current, new_pw)
        if success:
            QMessageBox.information(self, "Success", "Password changed successfully")
        else:
            QMessageBox.warning(self, "Error", err)

    def _on_change_username(self):
        from PySide6.QtWidgets import QInputDialog

        password, ok = QInputDialog.getText(
            self, "Change Username", "Enter your password:", QLineEdit.Password
        )
        if not ok or not password:
            return

        new_user, ok = QInputDialog.getText(
            self, "Change Username", "New username:"
        )
        if not ok or not new_user.strip():
            return

        success, err = self._auth.change_username(password, new_user.strip())
        if success:
            QMessageBox.information(self, "Success", f"Username changed to '{new_user.strip()}'")
        else:
            QMessageBox.warning(self, "Error", err)

    # ── Backup Actions ──

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

    def _get_last_backup_text(self) -> str:
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

    def _on_backup(self):
        dest_dir = QFileDialog.getExistingDirectory(self, "Select Backup Destination")
        if not dest_dir:
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(dest_dir) / f"archivium_backup_{timestamp}"

        try:
            shutil.copytree(str(DATA_DIR), str(backup_dir))
            self._db_size_label.setText(self._get_db_size())
            self._save_backup_timestamp()
            self._last_backup_label.setText(self._get_last_backup_text())
            QMessageBox.information(
                self, "Backup Complete", f"Backup saved to:\n{backup_dir}"
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
        if not (src / "walkin_records.db").exists():
            QMessageBox.warning(
                self, "Invalid Backup",
                "The selected folder does not contain a valid backup (missing walkin_records.db)."
            )
            return

        try:
            close_connection()
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
        try:
            with open(BACKUP_META_FILE, "w") as f:
                json.dump({"last_backup": datetime.now().isoformat()}, f)
        except Exception as e:
            logger.warning("Failed to save backup timestamp: %s", e)
