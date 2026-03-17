"""
Enhanced dashboard metric components with color coding and animations.
Provides visual hierarchy with size variation and critical alerts.
"""
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QSize, QTimer, QEvent
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
)

from app.ui.theme import Colors, Typography
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PulseAnimation:
    """Utility class to add pulse animation to a widget."""
    
    @staticmethod
    def start_pulse(widget: QWidget, duration: int = 1500):
        """Start a pulse animation on a widget (opacity variation)."""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.6)
        animation.setLoopCount(-1)  # Infinite loop
        animation.start()
        
        # Store reference to prevent garbage collection
        widget._pulse_animation = animation
        return animation


class MetricCard(QPushButton):
    """Enhanced metric card with color coding and size variation."""
    
    PRIORITY_CRITICAL = "critical"  # Red, large, pulsing
    PRIORITY_HIGH = "high"          # Orange, medium
    PRIORITY_MEDIUM = "medium"      # Blue, medium
    PRIORITY_LOW = "low"            # Gray, small
    
    def __init__(self, value: str, label: str, filter_key: str = "",
                 priority: str = "medium", alert: bool = False, parent=None):
        super().__init__(parent)
        self._value = value
        self._label = label
        self._filter_key = filter_key
        self._priority = priority
        self._alert = alert
        
        # Set size based on priority
        self._setup_size()
        self._setup_style()
        
        # If critical alert, start pulse animation
        if alert and priority == self.PRIORITY_CRITICAL:
            QTimer.singleShot(100, self._start_pulse)
    
    def _setup_size(self):
        """Set card size based on priority."""
        if self._priority == self.PRIORITY_CRITICAL:
            self.setMinimumHeight(140)
            self.setMinimumWidth(240)
        elif self._priority == self.PRIORITY_HIGH:
            self.setMinimumHeight(110)
            self.setMinimumWidth(180)
        else:  # MEDIUM and LOW
            self.setMinimumHeight(90)
            self.setMinimumWidth(160)
    
    def _setup_style(self):
        """Apply styling based on priority and alert status."""
        # Determine colors
        if self._alert and self._priority == self.PRIORITY_CRITICAL:
            value_color = Colors.DANGER
            bg_color = Colors.DANGER_LIGHT
            border_color = Colors.DANGER
        elif self._priority == self.PRIORITY_CRITICAL:
            value_color = Colors.DANGER
            bg_color = Colors.DANGER_LIGHT
            border_color = Colors.DANGER
        elif self._priority == self.PRIORITY_HIGH:
            value_color = Colors.WARNING
            bg_color = Colors.WARNING_LIGHT
            border_color = Colors.WARNING
        elif self._priority == self.PRIORITY_MEDIUM:
            value_color = Colors.ACCENT
            bg_color = Colors.BG_CARD
            border_color = Colors.ACCENT_LIGHT
        else:  # LOW
            value_color = Colors.TEXT_SECONDARY
            bg_color = Colors.BG_CARD
            border_color = Colors.BORDER_LIGHT
        
        # Determine font sizes
        if self._priority == self.PRIORITY_CRITICAL:
            value_size = 32
            label_size = 15
            padding = "20px 24px"
        elif self._priority == self.PRIORITY_HIGH:
            value_size = 28
            label_size = 14
            padding = "16px 20px"
        else:
            value_size = 24
            label_size = 13
            padding = "14px 18px"
        
        # Apply stylesheet
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: {padding};
                text-align: left;
                outline: none;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_CARD};
                border-color: {value_color};
            }}
            QPushButton:pressed {{
                background-color: {bg_color};
            }}
        """)
        
        # Setup card layout with values
        layout = QVBoxLayout(self)
        # Set proper internal margins so text isn't cramped at edges
        if self._priority == self.PRIORITY_CRITICAL:
            layout.setContentsMargins(20, 20, 20, 20)
        elif self._priority == self.PRIORITY_HIGH:
            layout.setContentsMargins(16, 16, 16, 16)
        else:
            layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        
        # Value label
        val_label = QLabel(self._value, self)
        val_font = QFont()
        val_font.setPointSize(value_size)
        val_font.setWeight(QFont.Bold)
        val_label.setFont(val_font)
        val_label.setStyleSheet(f"color: {value_color}; background: transparent;")
        layout.addWidget(val_label)
        
        # Description label
        desc_label = QLabel(self._label, self)
        desc_font = QFont()
        desc_font.setPointSize(label_size)
        desc_label.setFont(desc_font)
        desc_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; background: transparent;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Add drop shadow for critical cards
        if self._priority == self.PRIORITY_CRITICAL:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(20)
            shadow.setOffset(0, 4)
            shadow.setColor(QColor(0, 0, 0, 30))
            self.setGraphicsEffect(shadow)
        else:
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(12)
            shadow.setOffset(0, 2)
            shadow.setColor(QColor(0, 0, 0, 15))
            self.setGraphicsEffect(shadow)
    
    def _start_pulse(self):
        """Start pulse animation for critical alerts."""
        PulseAnimation.start_pulse(self, duration=1200)


class CriticalFocusZone(QFrame):
    """Top section highlighting critical metrics (expired visas, missing documents)."""
    
    clicked = Signal = None  # Set by parent
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("criticalZone")
        self.setStyleSheet(f"""
            #criticalZone {{
                background-color: {Colors.DANGER_LIGHT};
                border: 1px solid {Colors.DANGER};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        self._setup_layout()
    
    def _setup_layout(self):
        """Setup the critical zone layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("⚠️ Critical Alerts", self)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setWeight(QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {Colors.DANGER}; background: transparent;")
        layout.addWidget(title)
        
        self._content_layout = QVBoxLayout()
        self._content_layout.setSpacing(12)
        layout.addLayout(self._content_layout)
        layout.addStretch()
    
    def add_alert(self, label: str, count: str):
        """Add an alert item to the critical zone."""
        card = MetricCard(count, label, priority=MetricCard.PRIORITY_CRITICAL, alert=True)
        self._content_layout.addWidget(card)
    
    def clear(self):
        """Clear all alerts from the zone."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class MetricsGrid(QFrame):
    """Grid of metric cards with auto-layout based on priority."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("metricsGrid")
        
        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(16)
        self._layout.setContentsMargins(0, 0, 0, 0)
        
        self.setStyleSheet(f"""
            #metricsGrid {{
                background: transparent;
            }}
        """)
        
        self._cards = {}
    
    def add_metric(self, key: str, value: str, label: str,
                   priority: str = MetricCard.PRIORITY_MEDIUM,
                   alert: bool = False) -> MetricCard:
        """Add a metric card to the grid."""
        card = MetricCard(value, label, filter_key=key, priority=priority, alert=alert)
        self._cards[key] = card
        self._layout.addWidget(card)
        return card
    
    def add_section_title(self, title: str):
        """Add a section title."""
        label = QLabel(title, self)
        label_font = QFont()
        label_font.setPointSize(13)
        label_font.setWeight(QFont.Bold)
        label.setFont(label_font)
        label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; background: transparent; padding-top: 12px;")
        self._layout.addWidget(label)
    
    def update_metric(self, key: str, value: str):
        """Update a metric card's value."""
        if key in self._cards:
            self._cards[key]._value = value
            # Refresh the label
            layout = self._cards[key].layout()
            val_label = layout.itemAt(0).widget()
            if val_label:
                val_label.setText(value)
    
    def get_card(self, key: str) -> MetricCard | None:
        """Get a metric card by key."""
        return self._cards.get(key)
