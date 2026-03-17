"""
Dashboard page — primary landing screen after login.
Displays record summary, alerts, and recent activity.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout, QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor

from app.services.dashboard_service import DashboardService
from app.services.notification_service import NotificationService
from app.services.preferences_service import PreferencesService
from app.ui.theme import Colors
from app.ui.components.dashboard_metrics import MetricCard
from app.utils.logger import get_logger

logger = get_logger(__name__)


class DashboardPage(QWidget):
    """Operational dashboard with metrics, alerts, and recent activity."""

    filter_requested = Signal(str)   # emits filter type for record list
    record_selected = Signal(int)    # emits record_id for profile view
    view_notifications = Signal()    # navigate to notifications page

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dashboard = DashboardService()
        self._notifications = NotificationService()
        self._prefs = PreferencesService()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(0)

        # Header
        title = QLabel("Dashboard", self)
        title.setObjectName("pageTitle")
        outer.addWidget(title)

        # Scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget(scroll)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(16)
        self._content_layout.setContentsMargins(0, 0, 12, 0)

        scroll.setWidget(self._content)
        outer.addWidget(scroll, stretch=1)

    def load_data(self):
        """Refresh all dashboard data."""
        # Clear existing
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._render_summary()
        self._render_alerts()
        self._render_recent()
        self._content_layout.addStretch()

    def _render_summary(self):
        """Record Summary Panel with visual hierarchy and critical alerts."""
        summary = self._dashboard.get_record_summary()
        missing = self._dashboard.get_missing_docs_count()
        expired = self._dashboard.get_expired_visas_count()
        threshold = self._prefs.get_int("visa_expiry_threshold_days", 30)
        expiring = self._dashboard.get_expiring_visas_count(days=threshold)

        # Simple title
        section = QLabel("Summary", self._content)
        section.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {Colors.TEXT_SECONDARY}; background: transparent;"
        )
        self._content_layout.addWidget(section)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setContentsMargins(0, 0, 0, 0)

        # Expired Visas - High priority (orange/red) if any exist
        expired_card = MetricCard(
            str(expired), 
            "Expired Visas", 
            "expired_visa", 
            priority=MetricCard.PRIORITY_HIGH if expired > 0 else MetricCard.PRIORITY_LOW,
            parent=self._content
        )
        expired_card.clicked.connect(lambda: self.filter_requested.emit("expired_visa"))
        grid.addWidget(expired_card, 0, 0)

        # Missing Documents - High priority if any exist
        missing_card = MetricCard(
            str(missing), 
            "Missing Documents", 
            "missing_docs", 
            priority=MetricCard.PRIORITY_HIGH if missing > 0 else MetricCard.PRIORITY_LOW,
            parent=self._content
        )
        missing_card.clicked.connect(lambda: self.filter_requested.emit("missing_docs"))
        grid.addWidget(missing_card, 0, 1)

        # Expiring Soon - High priority (orange)
        expiring_card = MetricCard(
            str(expiring), 
            f"Expiring Soon ({threshold}d)", 
            "expiring_visa", 
            priority=MetricCard.PRIORITY_HIGH,
            parent=self._content
        )
        expiring_card.clicked.connect(lambda: self.filter_requested.emit("expiring_visa"))
        grid.addWidget(expiring_card, 0, 2)

        # Active Records - Medium priority (blue)
        active_card = MetricCard(str(summary["active"]), "Active Records", "active", priority=MetricCard.PRIORITY_MEDIUM, parent=self._content)
        active_card.clicked.connect(lambda: self.filter_requested.emit("active"))
        grid.addWidget(active_card, 1, 0)

        # Inactive Records - Low priority (gray)
        inactive_card = MetricCard(str(summary["inactive"]), "Archived Records", "inactive", priority=MetricCard.PRIORITY_LOW, parent=self._content)
        inactive_card.clicked.connect(lambda: self.filter_requested.emit("inactive"))
        grid.addWidget(inactive_card, 1, 1)

        grid_widget = QWidget(self._content)
        grid_widget.setLayout(grid)
        self._content_layout.addWidget(grid_widget)


    def _render_alerts(self):
        """Alerts & Attention Panel."""
        header = QHBoxLayout()
        section = QLabel("Alerts", self._content)
        section.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        header.addWidget(section)
        header.addStretch()

        view_all = QPushButton("View All", self._content)
        view_all.setStyleSheet(
            f"color: {Colors.ACCENT}; font-size: 13px; border: none; font-weight: 500;"
        )
        view_all.setCursor(Qt.PointingHandCursor)
        view_all.clicked.connect(self.view_notifications.emit)
        header.addWidget(view_all)

        header_widget = QWidget(self._content)
        header_widget.setLayout(header)
        self._content_layout.addWidget(header_widget)

        alerts = self._notifications.get_active_notifications(limit=5)
        if not alerts:
            empty = QLabel("No active alerts", self._content)
            empty.setStyleSheet(
                f"color: {Colors.TEXT_TERTIARY}; font-size: 14px; padding: 12px 0;"
            )
            self._content_layout.addWidget(empty)
            return

        for notif in alerts:
            row = self._create_alert_row(notif)
            self._content_layout.addWidget(row)

    def _create_alert_row(self, notif) -> QWidget:
        """Create a single alert row."""
        row = QWidget(self._content)
        row.setStyleSheet(
            f"background-color: {Colors.BG_CARD}; border-radius: 6px;"
        )
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        # Severity indicator
        severity_colors = {
            "critical": Colors.DANGER,
            "warning": Colors.WARNING,
            "info": Colors.ACCENT,
        }
        color = severity_colors.get(notif.severity, Colors.TEXT_SECONDARY)
        indicator = QLabel("●", row)
        indicator.setStyleSheet(f"color: {color}; font-size: 14px;")
        indicator.setFixedWidth(20)
        layout.addWidget(indicator)

        # Content
        info = QVBoxLayout()
        info.setSpacing(2)
        title = QLabel(notif.title, row)
        title.setStyleSheet("font-weight: 500;")
        info.addWidget(title)
        msg = QLabel(notif.message, row)
        msg.setObjectName("subtitleLabel")
        msg.setWordWrap(True)
        info.addWidget(msg)
        layout.addLayout(info, stretch=1)

        # Action: open record if linked
        if notif.record_id:
            open_btn = QPushButton("Open", row)
            open_btn.setFixedHeight(32)
            open_btn.setMinimumWidth(60)
            open_btn.clicked.connect(lambda: self.record_selected.emit(notif.record_id))
            layout.addWidget(open_btn)

        return row

    def _render_recent(self):
        """Recent Activity panel."""
        section = QLabel("Recent Activity", self._content)
        section.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        self._content_layout.addWidget(section)

        activities = self._dashboard.get_recent_activity(limit=10)
        if not activities:
            empty = QLabel("No recent activity", self._content)
            empty.setStyleSheet(
                f"color: {Colors.TEXT_TERTIARY}; font-size: 14px; padding: 12px 0;"
            )
            self._content_layout.addWidget(empty)
            return

        for act in activities:
            row = QWidget(self._content)
            row.setStyleSheet(
                f"background-color: {Colors.BG_CARD}; border-radius: 6px;"
            )
            layout = QHBoxLayout(row)
            layout.setContentsMargins(14, 8, 14, 8)
            layout.setSpacing(10)

            action_text = "Viewed" if act.get("action") == "viewed" else "Edited"
            name = f"{act.get('first_name', '')} {act.get('last_name', '')}".strip() or "Unknown"

            info = QLabel(f"{action_text}: {name}", row)
            info.setStyleSheet("font-size: 14px;")
            layout.addWidget(info, stretch=1)

            ts = act.get("timestamp", "")
            time_label = QLabel(ts[:16] if ts else "", row)
            time_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; font-size: 12px;")
            layout.addWidget(time_label)

            record_id = act.get("record_id")
            if record_id:
                btn = QPushButton("View", row)
                btn.setFixedHeight(28)
                btn.setMinimumWidth(50)
                btn.clicked.connect(lambda checked, rid=record_id: self.record_selected.emit(rid))
                layout.addWidget(btn)

            self._content_layout.addWidget(row)
