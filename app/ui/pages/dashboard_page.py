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
        outer.setSpacing(16)

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
        self._content_layout.setSpacing(20)
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
        self._render_trends()
        self._render_recent()
        self._content_layout.addStretch()

    def _render_summary(self):
        """Record Summary Panel."""
        section = QLabel("Records", self._content)
        section.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        self._content_layout.addWidget(section)

        grid = QGridLayout()
        grid.setSpacing(12)

        summary = self._dashboard.get_record_summary()
        missing = self._dashboard.get_missing_docs_count()
        expired = self._dashboard.get_expired_visas_count()
        threshold = self._prefs.get_int("visa_expiry_threshold_days", 30)
        expiring = self._dashboard.get_expiring_visas_count(days=threshold)

        stale_count = 0
        try:
            stale_count = len(self._dashboard.get_stale_records(days_threshold=90))
        except Exception:
            pass

        metrics = [
            (str(summary["active"]), "Active Records", "active", Colors.ACCENT),
            (str(summary["inactive"]), "Inactive Records", "inactive", Colors.TEXT_SECONDARY),
            (str(missing), "Missing Documents", "missing_docs", Colors.WARNING),
            (str(expired), "Expired Visas", "expired_visa", Colors.DANGER),
            (str(expiring), f"Expiring ({threshold}d)", "expiring_visa", Colors.WARNING),
            (str(stale_count), "Not Updated (90d)", "active", "#6B7280"),
        ]

        for i, (value, label, filter_key, color) in enumerate(metrics):
            card = self._create_metric_card(value, label, filter_key, color)
            grid.addWidget(card, i // 3, i % 3)

        grid_widget = QWidget(self._content)
        grid_widget.setLayout(grid)
        self._content_layout.addWidget(grid_widget)

    def _create_metric_card(self, value: str, label: str, filter_key: str, color: str) -> QWidget:
        """Create a clickable metric card."""
        card = QPushButton(parent=self._content)
        card.setCursor(Qt.PointingHandCursor)
        card.setFixedHeight(96)
        card.setStyleSheet(
            f"""QPushButton {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 10px;
                text-align: left;
                padding: 18px 20px;
            }}
            QPushButton:hover {{
                border-color: {color};
                background-color: #FAFBFF;
            }}"""
        )

        # Subtle drop shadow
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(16)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 13))  # rgba(0,0,0,0.05)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 10, 0, 0)
        card_layout.setSpacing(6)

        val_label = QLabel(value, card)
        val_label.setStyleSheet(
            f"font-size: 25px; font-weight: 700; color: {color}; background: transparent;"
        )
        card_layout.addWidget(val_label)

        desc_label = QLabel(label, card)
        desc_label.setStyleSheet(
            f"font-size: 13px; color: {Colors.TEXT_SECONDARY}; background: transparent;"
        )
        card_layout.addWidget(desc_label)

        card.clicked.connect(lambda checked, fk=filter_key: self.filter_requested.emit(fk))
        return card

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
            open_btn.clicked.connect(lambda checked, rid=notif.record_id: self.record_selected.emit(rid))
            layout.addWidget(open_btn)

        return row

    def _render_trends(self):
        """Record Trends line chart (6 months)."""
        MONTH_NAMES = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]

        def fmt_label(ym: str) -> str:
            """Convert 'YYYY-MM' to compact 'Mon \'YY', e.g. '2024-09' -> "Sep '24"."""
            try:
                year, month = ym.split("-")
                return f"{MONTH_NAMES[int(month) - 1]} '{year[2:]}"
            except Exception:
                return ym

        section = QLabel("Record Trends  -  Last 6 Months", self._content)
        section.setStyleSheet(
            f"font-size: 16px; font-weight: 600; color: {Colors.TEXT_PRIMARY};"
        )
        self._content_layout.addWidget(section)

        try:
            trend_data = self._dashboard.get_enrollment_trends(months_back=6)
        except Exception as e:
            logger.warning("Could not load trend data: %s", e)
            return
        labels = trend_data["labels"]
        values = trend_data["values"]
        friendly_labels = [fmt_label(lbl) for lbl in labels]

        try:
            from PySide6.QtCharts import (
                QChart, QChartView, QLineSeries, QCategoryAxis, QValueAxis,
            )
            from PySide6.QtCore import QMargins, QPointF
            from PySide6.QtGui import QPainter, QFont, QPen, QColor as QC

            # Build line series — clean, no clutter
            series = QLineSeries()
            series.setName("Records")
            pen = QPen(QC(Colors.ACCENT))
            pen.setWidth(2)
            series.setPen(pen)
            series.setPointsVisible(True)
            series.setPointLabelsVisible(False)   # no labels on points

            for i, v in enumerate(values):
                series.append(QPointF(i, v))

            chart = QChart()
            chart.addSeries(series)
            chart.setTitle("")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            chart.legend().setVisible(False)
            chart.setBackgroundRoundness(0)
            chart.setBackgroundVisible(False)     # card container provides the bg
            chart.setPlotAreaBackgroundVisible(False)
            chart.setMargins(QMargins(0, 0, 16, 0))

            # X axis  — category labels (month names)
            axis_x = QCategoryAxis()
            axis_x.setStartValue(0)
            for i, lbl in enumerate(friendly_labels):
                axis_x.append(lbl, i)
            x_font = QFont()
            x_font.setPointSize(9)
            axis_x.setLabelsFont(x_font)
            axis_x.setLabelsAngle(-15)
            chart.addAxis(axis_x, Qt.AlignBottom)
            series.attachAxis(axis_x)

            # Y axis
            axis_y = QValueAxis()
            axis_y.setLabelFormat("%d")
            axis_y.setTickCount(5)
            max_val = max(values) if values else 1
            axis_y.setRange(0, max(max_val + 2, 5))
            y_font = QFont()
            y_font.setPointSize(9)
            axis_y.setLabelsFont(y_font)
            chart.addAxis(axis_y, Qt.AlignLeft)
            series.attachAxis(axis_y)

            chart_view = QChartView(chart, self._content)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setFixedHeight(240)
            chart_view.setStyleSheet(
                f"background: {Colors.BG_CARD}; border-radius: 10px;"
                "border: 1px solid #E5E7EB;"
            )
            self._content_layout.addWidget(chart_view)

        except ImportError:
            fallback = QLabel(
                "  |  ".join(
                    f"{lbl}: {v} walk-in{'s' if v != 1 else ''}"
                    for lbl, v in zip(friendly_labels, values)
                ),
                self._content,
            )
            fallback.setWordWrap(True)
            fallback.setStyleSheet(
                f"color: {Colors.TEXT_SECONDARY}; font-size: 13px; padding: 12px 0;"
            )
            self._content_layout.addWidget(fallback)

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
