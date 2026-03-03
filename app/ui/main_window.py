"""
Main application window with sidebar navigation and page stacking.
Includes unsaved changes guard, read-only mode, undo, and backup reminders.
"""
import json
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QSplitter, QStatusBar, QPushButton, QLabel, QMessageBox,
)

from app.database import DATA_DIR
from app.ui.components.sidebar import Sidebar
from app.ui.pages.record_list import RecordListPage
from app.ui.pages.record_form import RecordForm
from app.ui.pages.profile_view import ProfileView
from app.ui.pages.backup_page import BackupPage
from app.utils.logger import get_logger

logger = get_logger(__name__)

BACKUP_META_FILE = DATA_DIR / "backup_meta.json"
BACKUP_REMIND_DAYS = 7
BACKUP_CHECK_INTERVAL_MS = 2 * 60 * 60 * 1000  # 2 hours


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Walk-In Records Management System")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self._read_only = False
        self._undo_action = None  # (type, data, timestamp)

        self._setup_ui()
        self._navigate_to("records")
        self._check_backup_reminder()

        # Periodic backup reminder check
        self._backup_timer = QTimer()
        self._backup_timer.setInterval(BACKUP_CHECK_INTERVAL_MS)
        self._backup_timer.timeout.connect(self._check_backup_reminder)
        self._backup_timer.start()

    def _setup_ui(self):
        # Central widget with splitter
        central = QWidget()
        layout = QHBoxLayout(central)
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
        self.setCentralWidget(central)

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

        # Read-only toggle button
        self._readonly_btn = QPushButton("Read-Only: Off")
        self._readonly_btn.setFixedHeight(24)
        self._readonly_btn.setStyleSheet("font-size: 12px; padding: 2px 8px;")
        self._readonly_btn.clicked.connect(self._toggle_read_only)
        self._status_bar.addPermanentWidget(self._readonly_btn)

        # Undo button (hidden by default)
        self._undo_btn = QPushButton("Undo")
        self._undo_btn.setFixedHeight(24)
        self._undo_btn.setStyleSheet(
            "font-size: 12px; padding: 2px 8px; color: #007AFF; font-weight: 600;"
        )
        self._undo_btn.setVisible(False)
        self._undo_btn.clicked.connect(self._perform_undo)
        self._status_bar.addPermanentWidget(self._undo_btn)

        # Undo expiry timer
        self._undo_timer = QTimer()
        self._undo_timer.setSingleShot(True)
        self._undo_timer.timeout.connect(self._clear_undo)

        # Create pages
        self._record_list = RecordListPage()
        self._record_list.record_selected.connect(self._show_profile)
        self._record_list.add_record_requested.connect(self._show_add_form)

        self._backup_page = BackupPage()

        # Add permanent pages
        self._content.addWidget(self._record_list)   # index 0
        self._content.addWidget(self._backup_page)    # index 1

    # ── Unsaved Changes Guard ──

    def _check_unsaved(self) -> bool:
        """Check if current widget has unsaved changes. Returns True if safe to proceed."""
        current = self._content.currentWidget()
        if isinstance(current, RecordForm):
            return current.confirm_discard()
        return True

    def closeEvent(self, event):
        """Guard app close against unsaved changes."""
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
        # Update current page
        self._record_list.set_read_only(self._read_only)

    # ── Undo ──

    def push_undo(self, action_type: str, description: str, undo_callback):
        """Register an undoable action (last one only, 30s expiry)."""
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

    # ── Backup Reminders ──

    def _check_backup_reminder(self):
        """Show a non-blocking status bar message if backup is overdue."""
        try:
            if BACKUP_META_FILE.exists():
                with open(BACKUP_META_FILE, "r") as f:
                    meta = json.load(f)
                last_backup = datetime.fromisoformat(meta.get("last_backup", ""))
                days_ago = (datetime.now() - last_backup).days
                if days_ago >= BACKUP_REMIND_DAYS:
                    self._status_bar.showMessage(
                        f"Reminder: Last backup was {days_ago} days ago. "
                        f"Consider creating a backup.", 10000
                    )
            else:
                self._status_bar.showMessage(
                    "Reminder: No backup has been created yet. "
                    "Consider creating a backup.", 10000
                )
        except Exception as e:
            logger.warning("Backup reminder check failed: %s", e)

    # ── Navigation ──

    def _navigate_to(self, page_id: str):
        """Navigate to a sidebar page."""
        if not self._check_unsaved():
            return

        if page_id == "records":
            self._content.setCurrentWidget(self._record_list)
            self._record_list.load_data()
            self._status_bar.showMessage("Records")
        elif page_id == "backup":
            self._content.setCurrentWidget(self._backup_page)
            self._status_bar.showMessage("Backup & Restore")

    def _show_profile(self, record_id: int):
        """Show the full profile view for a record."""
        if not self._check_unsaved():
            return

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
        """Show the add record form."""
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
        """Show the edit record form."""
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
        """Handle successful save — go to profile view."""
        self._content.removeWidget(form)
        form.deleteLater()
        self._show_profile(record_id)
        self._status_bar.showMessage("Record saved", 3000)

    def _on_edit_cancel(self, form: QWidget, record_id: int, previous_widget: QWidget):
        """Handle edit cancel — return to profile."""
        self._content.removeWidget(form)
        form.deleteLater()
        if previous_widget:
            # Remove old profile and create fresh one
            self._content.removeWidget(previous_widget)
            previous_widget.deleteLater()
        self._show_profile(record_id)

    def _return_to_list(self, widget: QWidget):
        """Return to the record list from any page."""
        self._content.removeWidget(widget)
        widget.deleteLater()
        self._content.setCurrentWidget(self._record_list)
        self._record_list.load_data()
        self._sidebar.set_active("records")
        self._status_bar.showMessage("Records")
