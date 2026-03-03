"""
Settings page — security, notification preferences, and about section.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGroupBox, QFormLayout,
    QCheckBox, QComboBox, QSpinBox, QLineEdit, QMessageBox,
)

from app.services.auth_service import AuthService
from app.services.preferences_service import PreferencesService
from app.constants import AUTO_LOCK_TIMEOUT_OPTIONS
from app.ui.theme import Colors
from app.utils.logger import get_logger

logger = get_logger(__name__)


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

    # ── About ──

    def _create_about_section(self) -> QGroupBox:
        group = QGroupBox("About")
        layout = QFormLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(16, 20, 16, 16)

        layout.addRow(QLabel("Application:"), QLabel("Archivium"))
        layout.addRow(QLabel("Version:"), QLabel("1.2"))

        from app.database import DATA_DIR
        dir_label = QLabel(str(DATA_DIR))
        dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addRow(QLabel("Data directory:"), dir_label)

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
