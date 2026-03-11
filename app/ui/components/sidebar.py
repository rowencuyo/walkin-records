"""
Sidebar navigation component — macOS Source List style.
"""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
    QSpacerItem, QSizePolicy,
)


class Sidebar(QWidget):
    """Source-list style sidebar navigation with section groupings."""

    page_changed = Signal(str)

    # (section_header | None, page_id, label)
    PAGES = [
        ("VIEWS", "dashboard", "Dashboard"),
        (None, "records", "Records"),
        (None, "notifications", "Notifications"),
        ("SYSTEM", "settings", "Settings"),
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
        title = QLabel("Archivium", self)
        title.setStyleSheet(
            "font-size: 18px; font-weight: 700; padding: 8px 20px 16px 20px; color: #1F2933;"
        )
        layout.addWidget(title)

        # Navigation buttons with section headers
        for entry in self.PAGES:
            section_header, page_id, label = entry

            # Insert section header if present
            if section_header:
                header = QLabel(section_header, self)
                header.setStyleSheet(
                    "font-size: 11px; font-weight: 700; color: #9CA3AF; "
                    "padding: 12px 20px 4px 20px; letter-spacing: 1px;"
                )
                layout.addWidget(header)

            btn_widget = QWidget(self)
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(10, 0, 12, 0)
            btn_layout.setSpacing(4)

            btn = QPushButton(label, btn_widget)
            btn.setProperty("active", False)
            btn.setCursor(btn.cursor())
            btn.clicked.connect(lambda checked, pid=page_id: self._on_click(pid))
            self._buttons[page_id] = btn
            btn_layout.addWidget(btn)

            # Badge (red dot) — always occupies space; color toggled on/off
            badge = QLabel("", btn_widget)
            badge.setFixedSize(8, 8)
            badge.setStyleSheet(
                "background-color: transparent; border-radius: 4px; "
                "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px;"
            )
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
        """Show or hide the red dot badge on a sidebar item."""
        badge = self._badges.get(page_id)
        if badge:
            if count > 0:
                badge.setStyleSheet(
                    "background-color: #EF4444; border-radius: 4px; "
                    "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px;"
                )
            else:
                badge.setStyleSheet(
                    "background-color: transparent; border-radius: 4px; "
                    "min-width: 8px; max-width: 8px; min-height: 8px; max-height: 8px;"
                )
