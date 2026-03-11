"""
Audit Log Viewer dialog — searchable, filterable table display of system audit logs.
"""
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QWidget,
)

from core.audit_logger import get_audit_logs, get_distinct_actions


class AuditViewerDialog(QDialog):
    """Modal dialog that displays the system audit log."""

    PAGE_SIZE = 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("System Audit Log")
        self.setMinimumSize(900, 560)
        self.resize(1000, 600)
        self._offset = 0
        self._total = 0
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("Audit Log", self)
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Filters row
        filters = QHBoxLayout()
        filters.setSpacing(12)

        self._search_input = QLineEdit(self)
        self._search_input.setPlaceholderText("Search logs…")
        self._search_input.setMaximumWidth(240)
        self._search_input.textChanged.connect(lambda: self._reset_and_load())
        filters.addWidget(self._search_input)

        self._action_combo = QComboBox(self)
        self._action_combo.addItem("All Actions", "")
        for action in get_distinct_actions():
            self._action_combo.addItem(action, action)
        self._action_combo.currentIndexChanged.connect(lambda: self._reset_and_load())
        filters.addWidget(self._action_combo)

        filters.addWidget(QLabel("From:", self))
        self._date_from = QDateEdit(self)
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("MM/dd/yyyy")
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_from.setFixedWidth(160)
        self._date_from.dateChanged.connect(lambda: self._reset_and_load())
        filters.addWidget(self._date_from)

        filters.addWidget(QLabel("To:", self))
        self._date_to = QDateEdit(self)
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("MM/dd/yyyy")
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setFixedWidth(160)
        self._date_to.dateChanged.connect(lambda: self._reset_and_load())
        filters.addWidget(self._date_to)

        filters.addStretch()
        layout.addLayout(filters)

        # Table
        self._table = QTableWidget(self)
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Module", "Record ID", "Details"
        ])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.horizontalHeader().setDefaultSectionSize(130)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setShowGrid(False)
        layout.addWidget(self._table, stretch=1)

        # Pagination
        pag = QHBoxLayout()
        self._count_label = QLabel("0 entries", self)
        self._count_label.setObjectName("subtitleLabel")
        pag.addWidget(self._count_label)
        pag.addStretch()

        self._prev_btn = QPushButton("Previous", self)
        self._prev_btn.setFixedHeight(32)
        self._prev_btn.clicked.connect(self._prev_page)
        pag.addWidget(self._prev_btn)

        self._page_label = QLabel("Page 1", self)
        self._page_label.setStyleSheet("font-size: 13px; color: #6B7280; padding: 0 8px;")
        pag.addWidget(self._page_label)

        self._next_btn = QPushButton("Next", self)
        self._next_btn.setFixedHeight(32)
        self._next_btn.clicked.connect(self._next_page)
        pag.addWidget(self._next_btn)

        layout.addLayout(pag)

        # Close
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("Close", self)
        close_btn.setFixedHeight(34)
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        layout.addLayout(close_row)

    # ── Data ──

    def _reset_and_load(self):
        self._offset = 0
        self._load()

    def _load(self):
        search = self._search_input.text().strip()
        action = self._action_combo.currentData() or ""
        date_from = self._date_from.date().toString("yyyy-MM-dd")
        date_to = self._date_to.date().toString("yyyy-MM-dd")

        rows, total = get_audit_logs(
            limit=self.PAGE_SIZE,
            offset=self._offset,
            search=search,
            action_filter=action,
            date_from=date_from,
            date_to=date_to,
        )
        self._total = total

        self._table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self._table.setItem(i, 0, QTableWidgetItem(row.get("timestamp", "")))
            self._table.setItem(i, 1, QTableWidgetItem(row.get("user", "")))
            self._table.setItem(i, 2, QTableWidgetItem(row.get("action", "")))
            self._table.setItem(i, 3, QTableWidgetItem(row.get("module", "")))
            rid = row.get("record_id")
            self._table.setItem(i, 4, QTableWidgetItem(str(rid) if rid else ""))
            self._table.setItem(i, 5, QTableWidgetItem(row.get("details", "") or ""))

        self._update_pagination()

    def _update_pagination(self):
        total_pages = max(1, (self._total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        current = (self._offset // self.PAGE_SIZE) + 1
        self._page_label.setText(f"Page {current} of {total_pages}")
        self._prev_btn.setEnabled(self._offset > 0)
        self._next_btn.setEnabled(current < total_pages)
        self._count_label.setText(f"{self._total} entries")

    def _prev_page(self):
        if self._offset >= self.PAGE_SIZE:
            self._offset -= self.PAGE_SIZE
            self._load()

    def _next_page(self):
        if self._offset + self.PAGE_SIZE < self._total:
            self._offset += self.PAGE_SIZE
            self._load()
