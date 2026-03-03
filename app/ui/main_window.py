"""
Main application window with login gate, session locking, sidebar navigation,
dashboard, notifications, and page stacking.
"""
import json
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QSplitter, QStatusBar, QPushButton, QLabel, QMessageBox,
)

from app.database import DATA_DIR
from app.ui.components.sidebar import Sidebar
from app.ui.pages.record_list import RecordListPage
from app.ui.pages.record_form import RecordForm
from app.ui.pages.profile_view import ProfileView
from app.ui.pages.login_page import LoginPage
from app.ui.pages.lock_screen import LockScreen
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.notification_page import NotificationPage
from app.ui.pages.settings_page import SettingsPage
from app.services.dashboard_service import DashboardService
from app.services.notification_service import NotificationService
from app.services.preferences_service import PreferencesService
from app.utils.logger import get_logger

logger = get_logger(__name__)

BACKUP_META_FILE = DATA_DIR / "backup_meta.json"
NOTIFICATION_SCAN_INTERVAL_MS = 5 * 60 * 1000  # 5 minutes


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Archivium 1.2")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self._read_only = False
        self._undo_action = None
        self._locked = False

        self._dashboard_service = DashboardService()
        self._notification_service = NotificationService()
        self._prefs = PreferencesService()

        self._setup_ui()
        self._show_login()

    def _setup_ui(self):
        # ── Root stack: login / lock / main ──
        self._root_stack = QStackedWidget()
        self.setCentralWidget(self._root_stack)

        # Login page
        self._login_page = LoginPage()
        self._login_page.login_successful.connect(self._on_login_success)
        self._root_stack.addWidget(self._login_page)  # index 0

        # Lock screen
        self._lock_screen = LockScreen()
        self._lock_screen.unlock_successful.connect(self._on_unlock)
        self._root_stack.addWidget(self._lock_screen)  # index 1

        # Main app container
        self._main_widget = QWidget()
        self._root_stack.addWidget(self._main_widget)  # index 2

        self._setup_main_ui()

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

        # Read-only indicator
        self._readonly_label = QLabel("")
        self._readonly_label.setStyleSheet(
            "color: #FF9500; font-weight: 600; padding: 0 8px;"
        )
        self._status_bar.addPermanentWidget(self._readonly_label)

        # Read-only toggle
        self._readonly_btn = QPushButton("Read-Only: Off")
        self._readonly_btn.setFixedHeight(24)
        self._readonly_btn.setStyleSheet("font-size: 12px; padding: 2px 8px;")
        self._readonly_btn.clicked.connect(self._toggle_read_only)
        self._status_bar.addPermanentWidget(self._readonly_btn)

        # Lock button
        lock_btn = QPushButton("Lock")
        lock_btn.setFixedHeight(24)
        lock_btn.setStyleSheet("font-size: 12px; padding: 2px 8px;")
        lock_btn.clicked.connect(self._lock_session)
        self._status_bar.addPermanentWidget(lock_btn)

        # Undo button (hidden by default)
        self._undo_btn = QPushButton("Undo")
        self._undo_btn.setFixedHeight(24)
        self._undo_btn.setStyleSheet(
            "font-size: 12px; padding: 2px 8px; color: #007AFF; font-weight: 600;"
        )
        self._undo_btn.setVisible(False)
        self._undo_btn.clicked.connect(self._perform_undo)
        self._status_bar.addPermanentWidget(self._undo_btn)

        # Undo timer
        self._undo_timer = QTimer()
        self._undo_timer.setSingleShot(True)
        self._undo_timer.timeout.connect(self._clear_undo)

        # Keyboard shortcut: Ctrl+L to lock
        self._lock_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        self._lock_shortcut.activated.connect(self._lock_session)

        # Notification scan timer
        self._scan_timer = QTimer()
        self._scan_timer.setInterval(NOTIFICATION_SCAN_INTERVAL_MS)
        self._scan_timer.timeout.connect(self._scan_notifications)

        # Idle auto-lock timer
        self._idle_timer = QTimer()
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

        # Install event filter for idle tracking
        self.installEventFilter(self)

    def _setup_main_ui(self):
        """Build the main app layout (sidebar + content)."""
        layout = QHBoxLayout(self._main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._navigate_to)
        splitter.addWidget(self._sidebar)

        # Content area
        self._content = QStackedWidget()
        splitter.addWidget(self._content)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 1100])

        layout.addWidget(splitter)

        # Create pages
        self._dashboard_page = DashboardPage()
        self._dashboard_page.filter_requested.connect(self._on_dashboard_filter)
        self._dashboard_page.record_selected.connect(self._show_profile)
        self._dashboard_page.view_notifications.connect(
            lambda: self._navigate_to("notifications")
        )

        self._record_list = RecordListPage()
        self._record_list.record_selected.connect(self._show_profile)
        self._record_list.add_record_requested.connect(self._show_add_form)

        self._notification_page = NotificationPage()
        self._notification_page.record_selected.connect(self._show_profile)

        self._settings_page = SettingsPage()

        # Add pages
        self._content.addWidget(self._dashboard_page)    # index 0
        self._content.addWidget(self._record_list)       # index 1
        self._content.addWidget(self._notification_page) # index 2
        self._content.addWidget(self._settings_page)     # index 3

    # ── Login / Lock ──

    def _show_login(self):
        self._root_stack.setCurrentIndex(0)

    def _on_login_success(self):
        self._root_stack.setCurrentIndex(2)
        self._navigate_to("dashboard")
        self._scan_notifications()
        self._scan_timer.start()
        self._reset_idle_timer()

    def _lock_session(self):
        """Lock the session — hide all data."""
        if self._locked:
            return
        self._locked = True
        self._idle_timer.stop()
        self._lock_screen.focus_password()
        self._root_stack.setCurrentIndex(1)
        self._status_bar.showMessage("Session locked")

    def _on_unlock(self):
        self._locked = False
        self._root_stack.setCurrentIndex(2)
        self._status_bar.showMessage("Session unlocked", 3000)
        self._reset_idle_timer()

    # ── Idle Auto-Lock ──

    def _reset_idle_timer(self):
        """Reset idle timer if auto-lock is enabled."""
        if self._prefs.get_bool("idle_lock_enabled") and not self._locked:
            timeout_min = self._prefs.get_int("idle_lock_timeout_min", 15)
            self._idle_timer.start(timeout_min * 60 * 1000)
        else:
            self._idle_timer.stop()

    def _on_idle_timeout(self):
        """Show warning before locking."""
        if self._locked:
            return
        reply = QMessageBox.question(
            self, "Idle Timeout",
            "You've been idle. The session will be locked.\n\n"
            "Click 'No' to stay active, or 'Yes' to lock now.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._lock_session()
        else:
            self._reset_idle_timer()

    def eventFilter(self, obj, event):
        """Reset idle timer on user interaction."""
        if (
            not self._locked
            and event.type() in (
                QEvent.MouseButtonPress, QEvent.KeyPress,
                QEvent.MouseMove, QEvent.Wheel,
            )
        ):
            self._reset_idle_timer()
        return super().eventFilter(obj, event)

    # ── Unsaved Changes Guard ──

    def _check_unsaved(self) -> bool:
        current = self._content.currentWidget()
        if isinstance(current, RecordForm):
            return current.confirm_discard()
        return True

    def closeEvent(self, event):
        if self._check_unsaved():
            event.accept()
        else:
            event.ignore()

    # ── Read-Only Mode ──

    def _toggle_read_only(self):
        self._read_only = not self._read_only
        if self._read_only:
            self._readonly_btn.setText("Read-Only: On")
            self._readonly_label.setText("[READ-ONLY]")
            self._status_bar.showMessage("Read-only mode enabled", 3000)
        else:
            self._readonly_btn.setText("Read-Only: Off")
            self._readonly_label.setText("")
            self._status_bar.showMessage("Read-only mode disabled", 3000)
        self._record_list.set_read_only(self._read_only)

    # ── Undo ──

    def push_undo(self, action_type: str, description: str, undo_callback):
        self._undo_action = {
            "type": action_type,
            "description": description,
            "callback": undo_callback,
        }
        self._undo_btn.setText(f"Undo: {description}")
        self._undo_btn.setVisible(True)
        self._undo_timer.start(30_000)

    def _perform_undo(self):
        if self._undo_action:
            try:
                self._undo_action["callback"]()
                self._status_bar.showMessage(
                    f"Undone: {self._undo_action['description']}", 3000
                )
            except Exception as e:
                logger.error("Undo failed: %s", e)
                QMessageBox.warning(self, "Undo Failed", str(e))
            finally:
                self._clear_undo()

    def _clear_undo(self):
        self._undo_action = None
        self._undo_btn.setVisible(False)
        self._undo_timer.stop()

    # ── Notifications ──

    def _scan_notifications(self):
        """Run notification scan and update badge."""
        try:
            self._notification_service.scan_and_generate()
            count = self._notification_service.get_unread_count()
            self._sidebar.set_badge("notifications", count)
        except Exception as e:
            logger.warning("Notification scan failed: %s", e)

    # ── Navigation ──

    def _navigate_to(self, page_id: str):
        if not self._check_unsaved():
            return

        self._sidebar.set_active(page_id)

        if page_id == "dashboard":
            self._content.setCurrentWidget(self._dashboard_page)
            self._dashboard_page.load_data()
            self._status_bar.showMessage("Dashboard")
        elif page_id == "records":
            self._content.setCurrentWidget(self._record_list)
            self._record_list.load_data()
            self._status_bar.showMessage("Records")
        elif page_id == "notifications":
            self._content.setCurrentWidget(self._notification_page)
            self._notification_page.load_data()
            self._scan_notifications()  # refresh badge
            self._status_bar.showMessage("Notifications")
        elif page_id == "settings":
            self._content.setCurrentWidget(self._settings_page)
            self._status_bar.showMessage("Settings")

    def _on_dashboard_filter(self, filter_type: str):
        """Navigate to records with a pre-applied filter."""
        self._sidebar.set_active("records")
        self._content.setCurrentWidget(self._record_list)
        self._record_list.apply_filter(filter_type)
        self._status_bar.showMessage(f"Records — {filter_type}")

    def _show_profile(self, record_id: int):
        if not self._check_unsaved():
            return

        # Track activity
        self._dashboard_service.record_activity(record_id, "viewed")

        profile = ProfileView(record_id, read_only=self._read_only)
        profile.back_requested.connect(lambda: self._return_to_list(profile))
        profile.edit_requested.connect(lambda rid: self._show_edit_form(rid, profile))
        profile.record_deleted.connect(lambda: self._return_to_list(profile))
        profile.undo_requested.connect(
            lambda atype, desc, cb: self.push_undo(atype, desc, cb)
        )

        self._content.addWidget(profile)
        self._content.setCurrentWidget(profile)
        self._status_bar.showMessage(f"Viewing record #{record_id}")

    def _show_add_form(self):
        if self._read_only:
            self._status_bar.showMessage("Cannot add records in read-only mode", 3000)
            return

        form = RecordForm()
        form.saved.connect(lambda rid: self._on_form_saved(rid, form))
        form.cancelled.connect(lambda: self._return_to_list(form))

        self._content.addWidget(form)
        self._content.setCurrentWidget(form)
        self._status_bar.showMessage("Adding new record")

    def _show_edit_form(self, record_id: int, previous_widget: QWidget = None):
        if self._read_only:
            self._status_bar.showMessage("Cannot edit records in read-only mode", 3000)
            return

        form = RecordForm(record_id=record_id)
        form.saved.connect(lambda rid: self._on_form_saved(rid, form))
        form.cancelled.connect(lambda: self._on_edit_cancel(form, record_id, previous_widget))

        self._content.addWidget(form)
        self._content.setCurrentWidget(form)
        self._status_bar.showMessage(f"Editing record #{record_id}")

    def _on_form_saved(self, record_id: int, form: QWidget):
        self._content.removeWidget(form)
        form.deleteLater()
        # Track activity
        self._dashboard_service.record_activity(record_id, "edited")
        self._show_profile(record_id)
        self._status_bar.showMessage("Record saved", 3000)

    def _on_edit_cancel(self, form: QWidget, record_id: int, previous_widget: QWidget):
        self._content.removeWidget(form)
        form.deleteLater()
        if previous_widget:
            self._content.removeWidget(previous_widget)
            previous_widget.deleteLater()
        self._show_profile(record_id)

    def _return_to_list(self, widget: QWidget):
        self._content.removeWidget(widget)
        widget.deleteLater()
        self._content.setCurrentWidget(self._record_list)
        self._record_list.load_data()
        self._sidebar.set_active("records")
        self._status_bar.showMessage("Records")
