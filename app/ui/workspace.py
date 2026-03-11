"""
Workspace – the main app layout container (post-login).

Structure
---------
  Workspace
    ├─ QSplitter (Horizontal)
    │    ├─ Sidebar
    │    └─ content_area  (QStackedWidget that fills the remaining space)
    └─ PreviewPanel  (overlay, parented to content_area, NOT in layout)

The PreviewPanel floats over content_area. It only appears when the Records
page is active and a row is selected.
"""
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QStackedWidget,
)

from app.ui.components.sidebar import Sidebar
from app.ui.components.preview_panel import PreviewPanel
from app.ui.pages.record_list import RecordListPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.notification_page import NotificationPage
from app.ui.pages.settings_page import SettingsPage
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Pages where PreviewPanel must NOT appear
_NO_PREVIEW_PAGES = {"dashboard", "notifications", "backup", "settings"}


class Workspace(QWidget):
    """
    Top-level workspace widget (replaces the old _main_widget in MainWindow).

    Signals re-emitted upward to MainWindow:
        navigate_requested(page_id)     – sidebar wants to navigate
        record_open_requested(record_id) – user double-clicked a record
        add_record_requested()           – user pressed "+ Add Record"
    """

    navigate_requested = Signal(str)
    record_open_requested = Signal(int)
    add_record_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._active_page = ""
        self._setup_ui()

    # ── Build UI ──────────────────────────────────────────────

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(1)

        # ── Sidebar ──
        self._sidebar = Sidebar(self)
        self._sidebar.page_changed.connect(self._on_sidebar_changed)
        splitter.addWidget(self._sidebar)

        # ── Content area (has a real layout so page_stack fills it) ──
        self._content_area = QWidget(self)
        self._content_area.setObjectName("contentArea")
        self._content_area.setStyleSheet(f"#contentArea {{ background-color: #F5F6F8; }}")
        ca_layout = QVBoxLayout(self._content_area)
        ca_layout.setContentsMargins(0, 0, 0, 0)
        ca_layout.setSpacing(0)
        splitter.addWidget(self._content_area)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 1100])

        layout.addWidget(splitter)

        # ── Pages inside content_area ──
        self._page_stack = QStackedWidget(self)
        ca_layout.addWidget(self._page_stack)

        # Dashboard
        self._dashboard_page = DashboardPage(self)
        self._dashboard_page.filter_requested.connect(
            lambda ft: self._apply_dashboard_filter(ft)
        )
        self._dashboard_page.record_selected.connect(self.record_open_requested)
        self._dashboard_page.view_notifications.connect(
            lambda: self._on_sidebar_changed("notifications")
        )
        self._page_stack.addWidget(self._dashboard_page)   # 0

        # Records
        self._record_list = RecordListPage(self)
        self._record_list.record_preview_requested.connect(self._on_preview_requested)
        self._record_list.record_open_requested.connect(self.record_open_requested)
        self._record_list.add_record_requested.connect(self.add_record_requested)
        self._page_stack.addWidget(self._record_list)      # 1

        # Notifications
        self._notification_page = NotificationPage(self)
        self._notification_page.record_selected.connect(self.record_open_requested)
        self._page_stack.addWidget(self._notification_page)  # 2

        # Settings (includes Backup)
        self._settings_page = SettingsPage(self)
        self._page_stack.addWidget(self._settings_page)      # 3

        # ── Preview Panel (overlay, parented to content_area) ──
        self._preview = PreviewPanel(self._content_area)
        self._preview.closed.connect(self._on_preview_closed)
        self._preview.open_requested.connect(self.record_open_requested)

        # Track content_area resize so the overlay stays pinned
        self._content_area.installEventFilter(self)

    # ── Event filter: keep overlay pinned when splitter resizes content_area ──

    def eventFilter(self, obj, event):
        if obj is self._content_area and event.type() == QEvent.Resize:
            if self._preview.isVisible():
                self._preview.update_geometry_for_parent()
        return super().eventFilter(obj, event)

    # ── Navigation ───────────────────────────────────────────

    def navigate_to(self, page_id: str):
        """Switch the visible page."""
        self._active_page = page_id
        self._sidebar.set_active(page_id)

        if page_id == "dashboard":
            self._page_stack.setCurrentWidget(self._dashboard_page)
            self._dashboard_page.load_data()
        elif page_id == "records":
            self._page_stack.setCurrentWidget(self._record_list)
            self._record_list.load_data()
        elif page_id == "notifications":
            self._page_stack.setCurrentWidget(self._notification_page)
            self._notification_page.load_data()
        elif page_id == "settings":
            self._page_stack.setCurrentWidget(self._settings_page)

        # Hide preview when leaving records
        if page_id in {"dashboard", "notifications", "settings"} and self._preview.isVisible():
            self._preview.hide_panel()

    def apply_filter(self, filter_type: str):
        """Navigate to records with a pre-applied filter (called from MainWindow)."""
        self.navigate_to("records")
        self._record_list.apply_filter(filter_type)

    def set_sidebar_badge(self, page_id: str, count: int):
        self._sidebar.set_badge(page_id, count)

    def set_read_only(self, enabled: bool):
        self._record_list.set_read_only(enabled)

    def refresh_record_list(self):
        self._record_list.load_data()

    def hide_preview(self):
        """Force the preview panel to hide."""
        if self._preview.isVisible():
            self._preview.hide_panel(animate=False)

    # ── Current page checks ──────────────────────────────────

    def current_page_widget(self) -> QWidget:
        return self._page_stack.currentWidget()

    # ── Internal slots ───────────────────────────────────────

    def _on_sidebar_changed(self, page_id: str):
        self.navigate_to(page_id)
        self.navigate_requested.emit(page_id)

    def _on_preview_requested(self, record_id: int):
        self._preview.show_record(record_id)

    def _on_preview_closed(self):
        pass  # panel closed itself; nothing else needed

    def _apply_dashboard_filter(self, filter_type: str):
        self.navigate_to("records")
        self._record_list.apply_filter(filter_type)
        self.navigate_requested.emit("records")
