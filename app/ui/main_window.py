"""
Main application window with sidebar navigation and page stacking.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QSplitter, QStatusBar,
)

from app.ui.components.sidebar import Sidebar
from app.ui.pages.record_list import RecordListPage
from app.ui.pages.record_form import RecordForm
from app.ui.pages.profile_view import ProfileView
from app.ui.pages.backup_page import BackupPage
from app.utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Walk-In Records Management System")
        self.setMinimumSize(1100, 700)
        self.resize(1300, 800)

        self._setup_ui()
        self._navigate_to("records")

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

        # Create pages
        self._record_list = RecordListPage()
        self._record_list.record_selected.connect(self._show_profile)
        self._record_list.add_record_requested.connect(self._show_add_form)

        self._backup_page = BackupPage()

        # Add permanent pages
        self._content.addWidget(self._record_list)   # index 0
        self._content.addWidget(self._backup_page)    # index 1

    def _navigate_to(self, page_id: str):
        """Navigate to a sidebar page."""
        if page_id == "records":
            self._content.setCurrentWidget(self._record_list)
            self._record_list.load_data()
            self._status_bar.showMessage("Records")
        elif page_id == "backup":
            self._content.setCurrentWidget(self._backup_page)
            self._status_bar.showMessage("Backup & Restore")

    def _show_profile(self, record_id: int):
        """Show the full profile view for a record."""
        profile = ProfileView(record_id)
        profile.back_requested.connect(lambda: self._return_to_list(profile))
        profile.edit_requested.connect(lambda rid: self._show_edit_form(rid, profile))
        profile.record_deleted.connect(lambda: self._return_to_list(profile))

        self._content.addWidget(profile)
        self._content.setCurrentWidget(profile)
        self._status_bar.showMessage(f"Viewing record #{record_id}")

    def _show_add_form(self):
        """Show the add record form."""
        form = RecordForm()
        form.saved.connect(lambda rid: self._on_form_saved(rid, form))
        form.cancelled.connect(lambda: self._return_to_list(form))

        self._content.addWidget(form)
        self._content.setCurrentWidget(form)
        self._status_bar.showMessage("Adding new record")

    def _show_edit_form(self, record_id: int, previous_widget: QWidget = None):
        """Show the edit record form."""
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
