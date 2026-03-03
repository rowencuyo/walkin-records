"""
Sidebar navigation component.
"""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QSpacerItem, QSizePolicy,
)


class Sidebar(QWidget):
    """Source-list style sidebar navigation."""

    page_changed = Signal(str)

    PAGES = [
        ("dashboard", "Dashboard"),
        ("records", "Records"),
        ("notifications", "Notifications"),
        ("settings", "Settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)
        self._buttons: dict[str, QPushButton] = {}
        self._badges: dict[str, QLabel] = {}
        self._current_page = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(2)

        # App title
        title = QLabel("Archivium")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 700; padding: 8px 20px 16px 20px; color: #1D1D1F;"
        )
        layout.addWidget(title)

        # Navigation buttons
        for page_id, label in self.PAGES:
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(0)

            btn = QPushButton(label)
            btn.setProperty("active", False)
            btn.setCursor(btn.cursor())
            btn.clicked.connect(lambda checked, pid=page_id: self._on_click(pid))
            self._buttons[page_id] = btn
            btn_layout.addWidget(btn)

            # Badge (for notification count)
            badge = QLabel("")
            badge.setStyleSheet(
                "background-color: #FF3B30; color: white; font-size: 11px; "
                "font-weight: 600; border-radius: 8px; padding: 1px 6px; "
                "min-width: 16px; max-height: 16px;"
            )
            badge.setAlignment(Qt.AlignCenter)
            badge.setVisible(False)
            badge.setFixedHeight(16)
            self._badges[page_id] = badge
            btn_layout.addWidget(badge)

            layout.addWidget(btn_widget)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Set initial
        self.set_active("dashboard")

    def _on_click(self, page_id: str):
        self.set_active(page_id)
        self.page_changed.emit(page_id)

    def set_active(self, page_id: str):
        """Set the active sidebar item."""
        self._current_page = page_id
        for pid, btn in self._buttons.items():
            is_active = pid == page_id
            btn.setProperty("active", str(is_active).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_badge(self, page_id: str, count: int):
        """Set a badge count on a sidebar item."""
        badge = self._badges.get(page_id)
        if badge:
            if count > 0:
                badge.setText(str(count) if count <= 99 else "99+")
                badge.setVisible(True)
            else:
                badge.setVisible(False)


# Need Qt import for alignment
from PySide6.QtCore import Qt
