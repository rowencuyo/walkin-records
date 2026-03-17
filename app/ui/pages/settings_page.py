"""
Settings page — security, notification preferences, and about section.
"""
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGroupBox, QFormLayout,
    QCheckBox, QComboBox, QSpinBox, QLineEdit, QMessageBox, QFileDialog, QDateEdit,
)

import json
import shutil
from datetime import datetime
from pathlib import Path

from app.database import DATA_DIR, DB_PATH, close_connection, initialize_database
from app.services.auth_service import AuthService
from app.services.preferences_service import PreferencesService
from app.services.export_service import ExportService
from app.constants import AUTO_LOCK_TIMEOUT_OPTIONS
from app.ui.theme import Colors
from app.utils.logger import get_logger
from core.audit_logger import log_action

logger = get_logger(__name__)

BACKUP_META_FILE = DATA_DIR / "backup_meta.json"


class SettingsPage(QWidget):
    """Application settings: security, notifications, about."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auth = AuthService()
        self._prefs = PreferencesService()
        self._export = ExportService()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(0)

        # Scroll
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget(scroll)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(0, 0, 12, 0)

        content_layout.addWidget(self._create_security_section())
        content_layout.addWidget(self._create_notification_section())
        content_layout.addWidget(self._create_alerts_section())
        content_layout.addWidget(self._create_export_section())
        content_layout.addWidget(self._create_backup_section())
        content_layout.addWidget(self._create_audit_section())
        content_layout.addWidget(self._create_about_section())
        content_layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

    def _make_section_header(self, text: str) -> QLabel:
        """Create a bold section title label."""
        label = QLabel(text, self)
        label.setObjectName("sectionTitle")
        label.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1F2933; "
            "padding: 0; margin: 0; background: transparent;"
        )
        return label

    def _make_divider(self) -> QFrame:
        """Create a subtle horizontal divider line."""
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #E5E7EB;")
        return line

    # ── Security ──

    def _create_security_section(self) -> QWidget:
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 16, 0, 16)

        layout.addWidget(self._make_section_header("Security"))
        layout.addSpacing(4)

        # Idle auto-lock
        lock_row = QHBoxLayout()
        self._idle_lock_cb = QCheckBox("Enable idle auto-lock", section)
        self._idle_lock_cb.setChecked(self._prefs.get_bool("idle_lock_enabled"))
        self._idle_lock_cb.stateChanged.connect(self._on_idle_lock_changed)
        lock_row.addWidget(self._idle_lock_cb)

        self._timeout_combo = QComboBox(section)
        self._timeout_combo.setMaximumWidth(120)
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
                QLabel("Username:", section),
                QLabel(meta.get("username", "admin"), section),
            )
            info_layout.addRow(
                QLabel("Password last changed:", section),
                QLabel(meta.get("password_changed_at", "Never")[:16], section),
            )
            info_layout.addRow(
                QLabel("Username last changed:", section),
                QLabel(meta.get("username_changed_at", "Never")[:16], section),
            )
            failed = meta.get("failed_attempts", 0)
            if failed:
                info_layout.addRow(
                    QLabel("Failed login attempts:", section),
                    QLabel(str(failed), section),
                )
            layout.addLayout(info_layout)

        # Change password
        btn_row = QHBoxLayout()
        change_pw_btn = QPushButton("Change Password", section)
        change_pw_btn.setFixedHeight(34)
        change_pw_btn.clicked.connect(self._on_change_password)
        btn_row.addWidget(change_pw_btn)

        change_user_btn = QPushButton("Change Username", section)
        change_user_btn.setFixedHeight(34)
        change_user_btn.clicked.connect(self._on_change_username)
        btn_row.addWidget(change_user_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addWidget(self._make_divider())
        return section

    # ── Notifications ──

    def _create_notification_section(self) -> QWidget:
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 16, 0, 16)

        layout.addWidget(self._make_section_header("Notifications"))
        layout.addSpacing(4)

        # Visa expiry toggle
        self._visa_cb = QCheckBox("Visa expiry & expiring notifications", section)
        self._visa_cb.setChecked(self._prefs.get_bool("notify_visa_expiry"))
        self._visa_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("notify_visa_expiry", self._visa_cb.isChecked())
        )
        layout.addWidget(self._visa_cb)

        # Threshold
        threshold_row = QHBoxLayout()
        threshold_row.addWidget(QLabel("Warn before visa expires:", section))
        self._threshold_spin = QSpinBox(section)
        self._threshold_spin.setMaximumWidth(120)
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
        self._docs_cb = QCheckBox("Missing documents notifications", section)
        self._docs_cb.setChecked(self._prefs.get_bool("notify_missing_docs"))
        self._docs_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("notify_missing_docs", self._docs_cb.isChecked())
        )
        layout.addWidget(self._docs_cb)

        # Backup reminder toggle
        self._backup_cb = QCheckBox("Backup reminders", section)
        self._backup_cb.setChecked(self._prefs.get_bool("notify_backup_reminder"))
        self._backup_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("notify_backup_reminder", self._backup_cb.isChecked())
        )
        layout.addWidget(self._backup_cb)

        # Retention
        retention_row = QHBoxLayout()
        retention_row.addWidget(QLabel("Notification history retention:", section))
        self._retention_spin = QSpinBox(section)
        self._retention_spin.setMaximumWidth(120)
        self._retention_spin.setRange(7, 365)
        self._retention_spin.setSuffix(" days")
        self._retention_spin.setValue(self._prefs.get_int("notification_retention_days", 90))
        self._retention_spin.valueChanged.connect(
            lambda v: self._prefs.set_int("notification_retention_days", v)
        )
        retention_row.addWidget(self._retention_spin)
        retention_row.addStretch()
        layout.addLayout(retention_row)

        layout.addWidget(self._make_divider())
        return section

    # ── Automated Alerts ──

    def _create_alerts_section(self) -> QWidget:
        """Create automated alerts and reminders settings."""
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 16, 0, 16)

        layout.addWidget(self._make_section_header("Automated Alerts"))
        layout.addSpacing(4)

        desc = QLabel(
            "Configure automatic alerts for visa expiry, missing documents, and other important events.",
            section
        )
        desc.setWordWrap(True)
        desc.setObjectName("subtitleLabel")
        layout.addWidget(desc)

        # Visa status alerts
        self._alert_visa_cb = QCheckBox("Visa status alerts (expired & expiring)", section)
        self._alert_visa_cb.setChecked(self._prefs.get_bool("alert_visa_status"))
        self._alert_visa_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("alert_visa_status", self._alert_visa_cb.isChecked())
        )
        layout.addWidget(self._alert_visa_cb)

        # Document alerts
        self._alert_docs_cb = QCheckBox("Missing document alerts", section)
        self._alert_docs_cb.setChecked(self._prefs.get_bool("alert_missing_documents"))
        self._alert_docs_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("alert_missing_documents", self._alert_docs_cb.isChecked())
        )
        layout.addWidget(self._alert_docs_cb)

        # Email digest
        self._alert_email_cb = QCheckBox("Daily email digest with important alerts", section)
        self._alert_email_cb.setChecked(self._prefs.get_bool("alert_email_digest"))
        self._alert_email_cb.stateChanged.connect(
            lambda: self._prefs.set_bool("alert_email_digest", self._alert_email_cb.isChecked())
        )
        layout.addWidget(self._alert_email_cb)

        # Digest time
        digest_row = QHBoxLayout()
        digest_row.addWidget(QLabel("Send digest at:", section))
        self._alert_digest_time = QComboBox(section)
        for hour in range(0, 24, 2):
            time_str = f"{hour:02d}:00"
            self._alert_digest_time.addItem(time_str, time_str)
        current_time = self._prefs.get("alert_digest_time", "09:00")
        idx = self._alert_digest_time.findData(current_time)
        if idx >= 0:
            self._alert_digest_time.setCurrentIndex(idx)
        self._alert_digest_time.currentIndexChanged.connect(
            lambda: self._prefs.set("alert_digest_time", self._alert_digest_time.currentData())
        )
        digest_row.addWidget(self._alert_digest_time)
        digest_row.addStretch()
        layout.addLayout(digest_row)

        layout.addWidget(self._make_divider())
        return section

    # ── Data & Export ──

    def _create_export_section(self) -> QWidget:
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 16, 0, 16)

        layout.addWidget(self._make_section_header("Data & Export"))
        layout.addSpacing(4)

        desc = QLabel(
            "Export walk-in records to the official Excel template. "
            "Select a date range to filter which records are included.",
            section
        )
        desc.setWordWrap(True)
        desc.setObjectName("subtitleLabel")
        layout.addWidget(desc)

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("From:", section))
        self._export_start = QDateEdit(section)
        self._export_start.setCalendarPopup(True)
        self._export_start.setDisplayFormat("MM/dd/yyyy")
        self._export_start.setDate(QDate.currentDate().addMonths(-1))
        self._export_start.setFixedWidth(160)
        date_row.addWidget(self._export_start)

        date_row.addSpacing(12)
        date_row.addWidget(QLabel("To:", section))
        self._export_end = QDateEdit(section)
        self._export_end.setCalendarPopup(True)
        self._export_end.setDisplayFormat("MM/dd/yyyy")
        self._export_end.setDate(QDate.currentDate())
        self._export_end.setFixedWidth(160)
        date_row.addWidget(self._export_end)
        date_row.addStretch()
        layout.addLayout(date_row)

        btn_row = QHBoxLayout()
        export_btn = QPushButton("Export Records", section)
        export_btn.setObjectName("primaryButton")
        export_btn.setFixedHeight(34)
        export_btn.clicked.connect(self._on_export)
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addWidget(self._make_divider())
        return section

    def _on_export(self):
        start = self._export_start.date().toString("yyyy-MM-dd")
        end = self._export_end.date().toString("yyyy-MM-dd")

        if self._export_start.date() > self._export_end.date():
            QMessageBox.warning(
                self, "Invalid Range",
                "Start date cannot be after end date.",
            )
            return

        records = self._export.get_records_by_date_range(start, end)
        if not records:
            QMessageBox.information(
                self, "No Records",
                "No records found in the selected date range.",
            )
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Export As",
            f"WalkIn_Records_Export_{start}_to_{end}.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not output_path:
            return

        try:
            count = self._export.export_to_excel(records, output_path)
            log_action(
                "admin", "EXPORT_DATA", "export",
                details=f"Exported {count} records ({start} to {end}) to {output_path}",
            )
            QMessageBox.information(
                self, "Export Complete",
                f"Successfully exported {count} records to:\n{output_path}",
            )
            logger.info("Exported %d records to %s", count, output_path)
        except Exception as e:
            logger.error("Export failed: %s", e)
            QMessageBox.critical(self, "Export Failed", f"Error: {e}")

    # ── Backup & Restore ──

    def _create_backup_section(self) -> QWidget:
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 16, 0, 16)

        layout.addWidget(self._make_section_header("Backup & Restore"))
        layout.addSpacing(4)

        desc = QLabel(
            "Create a backup of your database and files, or restore from a previous backup. "
            "Restoring will REPLACE all current data.",
            section
        )
        desc.setWordWrap(True)
        desc.setObjectName("subtitleLabel")
        layout.addWidget(desc)

        info_layout = QFormLayout()
        info_layout.setSpacing(6)

        self._db_size_label = QLabel(self._get_db_size(), section)
        info_layout.addRow(QLabel("Database size:", section), self._db_size_label)

        self._last_backup_label = QLabel(self._get_last_backup_text(), section)
        info_layout.addRow(QLabel("Last backup:", section), self._last_backup_label)
        layout.addLayout(info_layout)

        btn_row = QHBoxLayout()
        backup_btn = QPushButton("Create Backup", section)
        backup_btn.setObjectName("primaryButton")
        backup_btn.setFixedHeight(34)
        backup_btn.clicked.connect(self._on_backup)
        btn_row.addWidget(backup_btn)

        restore_btn = QPushButton("Restore", section)
        restore_btn.setObjectName("dangerButton")
        restore_btn.setFixedHeight(34)
        restore_btn.clicked.connect(self._on_restore)
        btn_row.addWidget(restore_btn)
        btn_row.addStretch()

        layout.addLayout(btn_row)

        layout.addWidget(self._make_divider())
        return section

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

    # ── Audit Log ──

    def _create_audit_section(self) -> QWidget:
        section = QWidget(self)
        layout = QVBoxLayout(section)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 16, 0, 16)

        layout.addWidget(self._make_section_header("Audit Log"))
        layout.addSpacing(4)

        desc = QLabel(
            "View a complete history of all system actions including record changes, "
            "logins, and settings updates.",
            section,
        )
        desc.setWordWrap(True)
        desc.setObjectName("subtitleLabel")
        layout.addWidget(desc)

        btn_row = QHBoxLayout()
        view_audit_btn = QPushButton("View System Audit Logs", section)
        view_audit_btn.setObjectName("primaryButton")
        view_audit_btn.setFixedHeight(34)
        view_audit_btn.clicked.connect(self._on_view_audit_logs)
        btn_row.addWidget(view_audit_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addWidget(self._make_divider())
        return section

    def _on_view_audit_logs(self):
        from app.ui.components.audit_viewer_dialog import AuditViewerDialog
        dialog = AuditViewerDialog(self)
        dialog.exec()

    # ── About ──

    def _create_about_section(self) -> QWidget:
        section = QWidget(self)
        layout = QFormLayout(section)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 16, 0, 16)

        header = self._make_section_header("About")
        layout.addRow(header)

        layout.addRow(QLabel("Application:", section), QLabel("Archivium", section))
        layout.addRow(QLabel("Version:", section), QLabel("1.2", section))

        from app.database import DATA_DIR
        dir_label = QLabel(str(DATA_DIR), section)
        dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addRow(QLabel("Data directory:", section), dir_label)

        return section

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
