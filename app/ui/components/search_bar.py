"""
Search bar component with filter dropdowns.
"""
from PySide6.QtCore import Signal, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout, QLineEdit, QComboBox, QWidget, QLabel,
)

from app.constants import (
    EducationalLevel, VisaStatus, YEAR_LEVELS, SEARCH_DEBOUNCE_MS,
)


class SearchBar(QWidget):
    """Search and filter toolbar for the record list."""

    search_changed = Signal(str, str, str, str, str)
    # Emits: (query, visa_status, educational_level, year_level, active_status)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(SEARCH_DEBOUNCE_MS)
        self._debounce_timer.timeout.connect(self._emit_search)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search input
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search anything — name, passport, country, visa, course...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMinimumWidth(250)
        self.search_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.search_input, stretch=2)

        # Visa status filter
        layout.addWidget(QLabel("Status:", self))
        self.visa_filter = QComboBox(self)
        self.visa_filter.addItem("All Statuses", "")
        for vs in VisaStatus:
            self.visa_filter.addItem(vs.value, vs.value)
        self.visa_filter.setMinimumWidth(160)
        self.visa_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.visa_filter)

        # Educational level filter
        layout.addWidget(QLabel("Level:", self))
        self.level_filter = QComboBox(self)
        self.level_filter.addItem("All Levels", "")
        for el in EducationalLevel:
            self.level_filter.addItem(el.value, el.value)
        self.level_filter.setMinimumWidth(140)
        self.level_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.level_filter)

        # Year level filter
        layout.addWidget(QLabel("Year:", self))
        self.year_filter = QComboBox(self)
        self.year_filter.addItem("All Years", "")
        for yl in YEAR_LEVELS:
            self.year_filter.addItem(yl, yl)
        self.year_filter.setMinimumWidth(120)
        self.year_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.year_filter)

        # Include inactive toggle
        self.inactive_filter = QComboBox(self)
        self.inactive_filter.addItem("Active Only", "active")
        self.inactive_filter.addItem("Archived Only", "archived")
        self.inactive_filter.addItem("All Records", "all")
        self.inactive_filter.setMinimumWidth(130)
        self.inactive_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.inactive_filter)

    def _on_text_changed(self):
        self._debounce_timer.start()

    def _on_filter_changed(self):
        self._emit_search()

    def _emit_search(self):
        query = self.search_input.text().strip()
        visa_status = self.visa_filter.currentData() or ""
        edu_level = self.level_filter.currentData() or ""
        year_level = self.year_filter.currentData() or ""
        active_status = self.inactive_filter.currentData() or "active"
        self.search_changed.emit(query, visa_status, edu_level, year_level, active_status)

    def clear_all(self):
        """Reset all filters."""
        self.search_input.clear()
        self.visa_filter.setCurrentIndex(0)
        self.level_filter.setCurrentIndex(0)
        self.year_filter.setCurrentIndex(0)
        self.inactive_filter.setCurrentIndex(0)
