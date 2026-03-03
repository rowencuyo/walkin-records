"""
Sidebar navigation component.
"""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QVBoxLayout, QWidget, QPushButton, QLabel, QSpacerItem, QSizePolicy,
)


class Sidebar(QWidget):
    """Source-list style sidebar navigation."""

    page_changed = Signal(str)

    PAGES = [
        ("records", "Records"),
        ("backup", "Backup"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)
        self._buttons: dict[str, QPushButton] = {}
        self._current_page = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(2)

        # App title
        title = QLabel("Walk-In Records")
        title.setStyleSheet(
            "font-size: 18px; font-weight: 700; padding: 8px 20px 16px 20px; color: #1D1D1F;"
        )
        layout.addWidget(title)

        # Navigation buttons
        for page_id, label in self.PAGES:
            btn = QPushButton(label)
            btn.setProperty("active", False)
            btn.setCursor(btn.cursor())
            btn.clicked.connect(lambda checked, pid=page_id: self._on_click(pid))
            self._buttons[page_id] = btn
            layout.addWidget(btn)

        layout.addSpacerItem(
            QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        # Set initial
        self.set_active("records")

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
