"""
Advanced Filters Panel - Clean, collapsible filter interface.
Provides filtering by country, document completeness, and date ranges.
"""
from PySide6.QtCore import Signal, Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QDateEdit,
)

from app.ui.theme import Colors, Typography
from app.utils.logger import get_logger

logger = get_logger(__name__)

COMMON_COUNTRIES = [
    "All Countries",
    "Philippines", "China", "India", "South Korea", "Japan",
    "Vietnam", "Thailand", "Indonesia", "Malaysia", "Singapore",
    "United States", "Canada", "Australia", "United Kingdom", "France",
    "Germany", "Italy", "Spain", "Netherlands", "Belgium", "Other"
]

COMPLETENESS_OPTIONS = [
    ("All", "all"),
    ("Complete", "complete"),
    ("Missing Fields", "missing_fields"),
    ("Incomplete Documents", "incomplete_documents"),
]


class AdvancedFiltersPanel(QWidget):
    """Collapsible advanced filters panel with country, completeness, and date filters."""
    
    filters_changed = Signal(dict)  # Emits filter dict when applied
    visibility_changed = Signal(bool)  # Emits True when expanded, False when collapsed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("advancedFiltersPanel")
        self._is_expanded = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Build the UI."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        
        # Toggle button
        toggle_layout = QHBoxLayout()
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setSpacing(8)
        
        self.toggle_btn = QPushButton("🔽 Advanced Filters", self)
        self.toggle_btn.setFixedHeight(36)
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.ACCENT};
                font-weight: 600;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_LIGHT};
            }}
        """)
        self.toggle_btn.clicked.connect(self._toggle_filters)
        toggle_layout.addWidget(self.toggle_btn)
        toggle_layout.addStretch()
        
        outer.addLayout(toggle_layout)
        
        # Filters container (collapsible)
        self._filters_widget = QWidget(self)
        filters_layout = QVBoxLayout(self._filters_widget)
        filters_layout.setContentsMargins(0, 16, 0, 16)
        filters_layout.setSpacing(16)
        
        # Country filter
        country_label = QLabel("Country of Citizenship", self)
        country_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Typography.SIZE_SM}px;
            font-weight: 600;
        """)
        filters_layout.addWidget(country_label)
        
        self.country_filter = QComboBox(self)
        self.country_filter.addItems(COMMON_COUNTRIES)
        self.country_filter.setMinimumHeight(40)
        self.country_filter.currentIndexChanged.connect(self._on_any_filter_changed)
        filters_layout.addWidget(self.country_filter)
        
        # Completeness filter
        completeness_label = QLabel("Document Completeness", self)
        completeness_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Typography.SIZE_SM}px;
            font-weight: 600;
            margin-top: 8px;
        """)
        filters_layout.addWidget(completeness_label)
        
        self.completeness_filter = QComboBox(self)
        for label_text, value in COMPLETENESS_OPTIONS:
            self.completeness_filter.addItem(label_text, value)
        self.completeness_filter.setMinimumHeight(40)
        self.completeness_filter.currentIndexChanged.connect(self._on_any_filter_changed)
        filters_layout.addWidget(self.completeness_filter)
        
        # Date range label
        date_label = QLabel("Date Range", self)
        date_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Typography.SIZE_SM}px;
            font-weight: 600;
            margin-top: 8px;
        """)
        filters_layout.addWidget(date_label)
        
        # Arrival Date row
        arrival_row = QHBoxLayout()
        arrival_row.setSpacing(12)
        arrival_row.setContentsMargins(0, 0, 0, 0)
        
        arrival_label = QLabel("Arrival Date:", self)
        arrival_label.setFixedWidth(120)
        arrival_row.addWidget(arrival_label)
        
        self.arrival_from = QDateEdit(self)
        self.arrival_from.setDate(QDate.currentDate().addMonths(-3))
        self.arrival_from.setCalendarPopup(True)
        self.arrival_from.setMinimumHeight(40)
        self.arrival_from.dateChanged.connect(self._on_any_filter_changed)
        arrival_row.addWidget(self.arrival_from, 1)
        
        to_label_1 = QLabel("to", self)
        to_label_1.setFixedWidth(25)
        to_label_1.setAlignment(Qt.AlignCenter)
        arrival_row.addWidget(to_label_1)
        
        self.arrival_to = QDateEdit(self)
        self.arrival_to.setDate(QDate.currentDate())
        self.arrival_to.setCalendarPopup(True)
        self.arrival_to.setMinimumHeight(40)
        self.arrival_to.dateChanged.connect(self._on_any_filter_changed)
        arrival_row.addWidget(self.arrival_to, 1)
        
        arrival_row.addStretch()
        filters_layout.addLayout(arrival_row)
        
        # Record Created row
        created_row = QHBoxLayout()
        created_row.setSpacing(12)
        created_row.setContentsMargins(0, 0, 0, 0)
        
        created_label = QLabel("Record Created:", self)
        created_label.setFixedWidth(120)
        created_row.addWidget(created_label)
        
        self.created_from = QDateEdit(self)
        self.created_from.setDate(QDate.currentDate().addMonths(-3))
        self.created_from.setCalendarPopup(True)
        self.created_from.setMinimumHeight(40)
        self.created_from.dateChanged.connect(self._on_any_filter_changed)
        created_row.addWidget(self.created_from, 1)
        
        to_label_2 = QLabel("to", self)
        to_label_2.setFixedWidth(25)
        to_label_2.setAlignment(Qt.AlignCenter)
        created_row.addWidget(to_label_2)
        
        self.created_to = QDateEdit(self)
        self.created_to.setDate(QDate.currentDate())
        self.created_to.setCalendarPopup(True)
        self.created_to.setMinimumHeight(40)
        self.created_to.dateChanged.connect(self._on_any_filter_changed)
        created_row.addWidget(self.created_to, 1)
        
        created_row.addStretch()
        filters_layout.addLayout(created_row)
        
        # Add spacing before buttons
        filters_layout.addSpacing(24)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        
        self.apply_btn = QPushButton("Apply Filters", self)
        self.apply_btn.setFixedHeight(40)
        self.apply_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {Colors.ACCENT_LIGHT};
            }}
        """)
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        buttons_layout.addWidget(self.apply_btn)
        
        self.reset_btn = QPushButton("Reset All", self)
        self.reset_btn.setFixedHeight(40)
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background-color: {Colors.BG_HOVER};
            }}
        """)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        buttons_layout.addWidget(self.reset_btn)
        
        buttons_layout.addStretch()
        filters_layout.addLayout(buttons_layout)
        
        # Initially hidden
        self._filters_widget.hide()
        
        outer.addWidget(self._filters_widget)
        outer.addStretch()
    
    def _on_any_filter_changed(self):
        """Called when any filter control changes."""
        logger.debug("A filter control was changed")
    
    def _toggle_filters(self):
        """Toggle panel visibility."""
        self._is_expanded = not self._is_expanded
        
        if self._is_expanded:
            self._filters_widget.show()
            self.toggle_btn.setText("🔼 Advanced Filters")
        else:
            self._filters_widget.hide()
            self.toggle_btn.setText("🔽 Advanced Filters")
        
        self.visibility_changed.emit(self._is_expanded)
        logger.debug(f"Filters toggled: {'expanded' if self._is_expanded else 'collapsed'}")
    
    def _on_apply_clicked(self):
        """Emit filters when Apply is clicked."""
        # Get country value
        country = self.country_filter.currentText()
        if country == "All Countries":
            country = ""
        
        # Get completeness value  
        completeness = self.completeness_filter.currentData()
        
        filters = {
            "country": country,
            "completeness": completeness if completeness else "all",
            "arrival_date_from": self.arrival_from.date().toString(Qt.ISODate),
            "arrival_date_to": self.arrival_to.date().toString(Qt.ISODate),
            "created_date_from": self.created_from.date().toString(Qt.ISODate),
            "created_date_to": self.created_to.date().toString(Qt.ISODate),
        }
        self.filters_changed.emit(filters)
        logger.debug(f"Filters applied: {filters}")
    
    def _on_reset_clicked(self):
        """Reset all filters to defaults."""
        self.country_filter.setCurrentIndex(0)
        self.completeness_filter.setCurrentIndex(0)
        self.arrival_from.setDate(QDate.currentDate().addMonths(-3))
        self.arrival_to.setDate(QDate.currentDate())
        self.created_from.setDate(QDate.currentDate().addMonths(-3))
        self.created_to.setDate(QDate.currentDate())
        logger.debug("Filters reset to defaults")
    
    def get_filters(self) -> dict:
        """Get current filter values."""
        return {
            "country": self.country_filter.currentText() if self.country_filter.currentText() != "All Countries" else "",
            "completeness": self.completeness_filter.currentData(),
            "arrival_date_from": self.arrival_from.date().toString(Qt.ISODate),
            "arrival_date_to": self.arrival_to.date().toString(Qt.ISODate),
            "created_date_from": self.created_from.date().toString(Qt.ISODate),
            "created_date_to": self.created_to.date().toString(Qt.ISODate),
        }
