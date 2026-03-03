"""
Notification list page — grouped, severity-ordered, with lifecycle actions.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTabBar, QStackedWidget,
)

from app.services.notification_service import NotificationService
from app.ui.theme import Colors
from app.utils.logger import get_logger

logger = get_logger(__name__)


class NotificationPage(QWidget):
    """Notification list with tabs: Active, Dismissed, History."""

    record_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._service = NotificationService()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Notifications")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        mark_all_btn = QPushButton("Mark All Read")
        mark_all_btn.setFixedHeight(34)
        mark_all_btn.clicked.connect(self._mark_all_read)
        header.addWidget(mark_all_btn)

        outer.addLayout(header)

        # Tabs
        self._tabs = QTabBar()
        self._tabs.addTab("Active")
        self._tabs.addTab("Dismissed")
        self._tabs.addTab("History")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        outer.addWidget(self._tabs)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._list_widget = QWidget()
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setSpacing(6)
        self._list_layout.setContentsMargins(0, 0, 12, 0)

        scroll.setWidget(self._list_widget)
        outer.addWidget(scroll, stretch=1)

    def load_data(self):
        """Refresh the notification list for the current tab."""
        self._on_tab_changed(self._tabs.currentIndex())

    def _on_tab_changed(self, index: int):
        # Clear
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if index == 0:
            notifications = self._service.get_active_notifications(limit=50)
        elif index == 1:
            notifications = self._service.get_notifications(status_filter="dismissed", limit=50)
        else:
            notifications = self._service.get_notifications(status_filter="resolved", limit=50)

        if not notifications:
            empty = QLabel("No notifications" if index == 0 else "No items")
            empty.setStyleSheet(
                f"color: {Colors.TEXT_TERTIARY}; font-size: 14px; padding: 24px 0;"
            )
            empty.setAlignment(Qt.AlignCenter)
            self._list_layout.addWidget(empty)
            self._list_layout.addStretch()
            return

        for notif in notifications:
            row = self._create_notification_row(notif, show_actions=(index == 0))
            self._list_layout.addWidget(row)

        self._list_layout.addStretch()

    def _create_notification_row(self, notif, show_actions: bool = True) -> QWidget:
        row = QWidget()
        unread = notif.status == "unread"
        bg = Colors.BG_CARD if not unread else "#F0F5FF"
        row.setStyleSheet(
            f"background-color: {bg}; border-radius: 6px;"
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Severity pill
        severity_config = {
            "critical": (Colors.DANGER, "CRITICAL"),
            "warning": (Colors.WARNING, "WARNING"),
            "info": (Colors.ACCENT, "INFO"),
        }
        color, label_text = severity_config.get(notif.severity, (Colors.TEXT_SECONDARY, "INFO"))
        pill = QLabel(label_text)
        pill.setStyleSheet(
            f"background-color: {color}; color: white; padding: 2px 8px; "
            f"border-radius: 4px; font-size: 11px; font-weight: 600;"
        )
        pill.setFixedHeight(20)
        pill.setFixedWidth(70)
        pill.setAlignment(Qt.AlignCenter)
        layout.addWidget(pill)

        # Content
        info = QVBoxLayout()
        info.setSpacing(2)
        title = QLabel(notif.title)
        title.setStyleSheet(
            f"font-weight: {'600' if unread else '400'}; font-size: 14px;"
        )
        info.addWidget(title)

        msg = QLabel(notif.message)
        msg.setObjectName("subtitleLabel")
        msg.setWordWrap(True)
        info.addWidget(msg)

        ts = QLabel(notif.created_at[:16] if notif.created_at else "")
        ts.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; font-size: 11px;")
        info.addWidget(ts)

        layout.addLayout(info, stretch=1)

        # Actions
        if show_actions:
            if notif.record_id:
                open_btn = QPushButton("Open")
                open_btn.setFixedHeight(29)
                open_btn.setMinimumWidth(55)
                open_btn.clicked.connect(lambda: self.record_selected.emit(notif.record_id))
                layout.addWidget(open_btn)

            dismiss_btn = QPushButton("Dismiss")
            dismiss_btn.setFixedHeight(29)
            dismiss_btn.setMinimumWidth(70)
            dismiss_btn.clicked.connect(
                lambda checked, nid=notif.id: self._dismiss(nid)
            )
            layout.addWidget(dismiss_btn)

        return row

    def _dismiss(self, notification_id: int):
        self._service.mark_dismissed(notification_id)
        self.load_data()

    def _mark_all_read(self):
        self._service.mark_all_read()
        self.load_data()
