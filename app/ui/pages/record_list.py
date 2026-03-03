"""
Record List page with Table View and Card View toggle.
Integrates search proxy, completeness indicators, and read-only mode.
"""
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QPushButton, QLabel, QComboBox, QAbstractItemView, QScrollArea,
    QGridLayout, QFrame, QSpacerItem, QSizePolicy, QStackedWidget,
)

from app.constants import DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS
from app.models import WalkInRecord
from app.services.record_service import RecordService
from app.services.image_service import ImageService
from app.ui.components.search_bar import SearchBar
from app.ui.models.record_table_model import RecordTableModel
from app.ui.models.record_proxy_model import RecordProxyModel
from app.ui.theme import Colors


class RecordCard(QFrame):
    """Individual card for the card view."""
    clicked = Signal(int)

    def __init__(self, record: WalkInRecord, pic_path: str | None = None,
                 completeness: str = "", parent=None):
        super().__init__(parent)
        self._record_id = record.id
        self.setObjectName("recordCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(200)
        self.setStyleSheet(f"""
            #recordCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 10px;
            }}
            #recordCard:hover {{
                border-color: {Colors.ACCENT};
                background-color: {Colors.SELECTION};
            }}
        """)
        self._setup_ui(record, pic_path, completeness)

    def _setup_ui(self, record: WalkInRecord, pic_path: str | None,
                  completeness: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop)

        # Top row: avatar + name + completeness badge
        top = QHBoxLayout()
        top.setSpacing(10)

        # Small avatar
        avatar = QLabel()
        avatar.setFixedSize(40, 40)
        if pic_path:
            pix = QPixmap(pic_path).scaled(40, 40, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (pix.width() - 40) // 2
            y = (pix.height() - 40) // 2
            cropped = pix.copy(x, y, 40, 40)
            result = QPixmap(40, 40)
            result.fill(Qt.transparent)
            painter = QPainter(result)
            painter.setRenderHint(QPainter.Antialiasing)
            clip = QPainterPath()
            clip.addEllipse(0, 0, 40, 40)
            painter.setClipPath(clip)
            painter.drawPixmap(0, 0, cropped)
            painter.end()
            avatar.setPixmap(result)
        else:
            avatar.setText("?")
            avatar.setAlignment(Qt.AlignCenter)
            avatar.setStyleSheet(
                "background-color: #E5E5EA; border-radius: 20px; color: #8E8E93; font-size: 18px; font-weight: 600;"
            )
        top.addWidget(avatar)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_label = QLabel(record.full_name)
        name_label.setStyleSheet("font-weight: 600; font-size: 16px; color: #1D1D1F;")
        name_label.setWordWrap(True)
        name_col.addWidget(name_label)

        passport_label = QLabel(record.passport_number)
        passport_label.setStyleSheet("font-size: 14px; color: #6E6E73;")
        name_col.addWidget(passport_label)
        top.addLayout(name_col, stretch=1)

        # Completeness badge
        if completeness == "complete":
            badge = QLabel("Complete Docs")
            badge.setStyleSheet(
                "background-color: #34C759; color: white; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
            badge.setFixedHeight(20)
            top.addWidget(badge, alignment=Qt.AlignTop)
        elif completeness == "missing_fields":
            badge = QLabel("Missing Fields")
            badge.setStyleSheet(
                "background-color: #FF9500; color: white; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
            badge.setFixedHeight(20)
            top.addWidget(badge, alignment=Qt.AlignTop)
        elif completeness == "incomplete_documents":
            badge = QLabel("Incomplete Docs")
            badge.setStyleSheet(
                "background-color: #FF9500; color: white; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
            badge.setFixedHeight(20)
            top.addWidget(badge, alignment=Qt.AlignTop)
        elif completeness == "no_documents":
            badge = QLabel("No Docs")
            badge.setStyleSheet(
                "background-color: #FF9500; color: white; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
            badge.setFixedHeight(20)
            top.addWidget(badge, alignment=Qt.AlignTop)

        layout.addLayout(top)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")
        layout.addWidget(div)

        # Details
        details = [
            ("Visa", record.visa_category[:25] + "..." if len(record.visa_category) > 25 else record.visa_category),
            ("Status", record.visa_status),
            ("Course", record.course_program[:20] + "..." if len(record.course_program) > 20 else record.course_program),
            ("Year", record.year_level),
        ]
        for label_text, value in details:
            if value:
                row = QHBoxLayout()
                row.setSpacing(6)
                lbl = QLabel(f"{label_text}:")
                lbl.setStyleSheet("font-size: 13px; color: #8E8E93; min-width: 40px;")
                row.addWidget(lbl)
                val = QLabel(value)
                val.setStyleSheet("font-size: 13px; color: #1D1D1F;")
                val.setWordWrap(True)
                row.addWidget(val, stretch=1)
                layout.addLayout(row)

    def mousePressEvent(self, event):
        if self._record_id is not None:
            self.clicked.emit(self._record_id)
        super().mousePressEvent(event)


class RecordListPage(QWidget):
    """Main record list with table and card views."""

    record_selected = Signal(int)
    add_record_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._record_service = RecordService()
        self._image_service = ImageService()

        # State
        self._current_page = 0
        self._page_size = DEFAULT_PAGE_SIZE
        self._total_count = 0
        self._query = ""
        self._visa_status = ""
        self._edu_level = ""
        self._year_level = ""
        self._include_inactive = False
        self._current_records: list[WalkInRecord] = []
        self._doc_counts: dict[int, int] = {}
        self._pic_path_cache: dict[int, str | None] = {}
        self._completeness_cache: dict[int, str] = {}

        # Debounce timer for card rebuild on resize
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(300)
        self._resize_timer.timeout.connect(self._populate_cards)

        self._setup_ui()
        self.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(16)

        # Header row
        header = QHBoxLayout()
        title = QLabel("Records")
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        # View toggle
        self._table_btn = QPushButton("Table")
        self._table_btn.setCheckable(True)
        self._table_btn.setChecked(True)
        self._table_btn.setFixedHeight(36)
        self._table_btn.clicked.connect(lambda: self._switch_view(0))

        self._card_btn = QPushButton("Cards")
        self._card_btn.setCheckable(True)
        self._card_btn.setFixedHeight(36)
        self._card_btn.clicked.connect(lambda: self._switch_view(1))

        header.addWidget(self._table_btn)
        header.addWidget(self._card_btn)

        # Add button
        self._add_btn = QPushButton("+ Add Record")
        self._add_btn.setObjectName("primaryButton")
        self._add_btn.setFixedHeight(38)
        self._add_btn.clicked.connect(self.add_record_requested.emit)
        header.addWidget(self._add_btn)

        layout.addLayout(header)

        # Search bar
        self._search_bar = SearchBar()
        self._search_bar.search_changed.connect(self._on_search_changed)
        layout.addWidget(self._search_bar)

        # View stack
        self._view_stack = QStackedWidget()

        # --- Table View ---
        self._table_model = RecordTableModel()
        self._proxy_model = RecordProxyModel()
        self._proxy_model.setSourceModel(self._table_model)

        self._table_view = QTableView()
        self._table_view.setModel(self._proxy_model)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table_view.setSortingEnabled(True)
        self._table_view.verticalHeader().setVisible(False)
        self._table_view.setShowGrid(False)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table_view.horizontalHeader().setDefaultSectionSize(140)
        self._table_view.horizontalHeader().setMinimumSectionSize(80)
        self._table_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self._table_view.doubleClicked.connect(self._on_table_double_click)

        # Set completeness column width (narrow)
        self._table_view.horizontalHeader().resizeSection(0, 40)
        self._table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

        self._view_stack.addWidget(self._table_view)

        # --- Card View ---
        self._card_scroll = QScrollArea()
        self._card_scroll.setWidgetResizable(True)
        self._card_scroll.setFrameShape(QFrame.NoFrame)
        self._card_container = QWidget()
        self._card_layout = QGridLayout(self._card_container)
        self._card_layout.setSpacing(12)
        self._card_layout.setContentsMargins(0, 0, 0, 0)
        self._card_scroll.setWidget(self._card_container)
        self._view_stack.addWidget(self._card_scroll)

        layout.addWidget(self._view_stack, stretch=1)

        # Pagination
        pag = QHBoxLayout()
        pag.setSpacing(8)

        self._record_count_label = QLabel("0 records")
        self._record_count_label.setObjectName("subtitleLabel")
        pag.addWidget(self._record_count_label)

        pag.addStretch()

        self._prev_btn = QPushButton("Previous")
        self._prev_btn.setFixedHeight(34)
        self._prev_btn.clicked.connect(self._prev_page)
        pag.addWidget(self._prev_btn)

        self._page_label = QLabel("Page 1")
        self._page_label.setStyleSheet("font-size: 14px; color: #6E6E73; padding: 0 8px;")
        pag.addWidget(self._page_label)

        self._next_btn = QPushButton("Next")
        self._next_btn.setFixedHeight(34)
        self._next_btn.clicked.connect(self._next_page)
        pag.addWidget(self._next_btn)

        pag.addWidget(QLabel("Per page:"))
        self._page_size_combo = QComboBox()
        for ps in PAGE_SIZE_OPTIONS:
            self._page_size_combo.addItem(str(ps), ps)
        self._page_size_combo.setCurrentText(str(self._page_size))
        self._page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        pag.addWidget(self._page_size_combo)

        layout.addLayout(pag)

    # -- Read-Only Mode --

    def set_read_only(self, enabled: bool):
        """Show or hide the add button based on read-only mode."""
        self._add_btn.setVisible(not enabled)

    # -- View Toggle --

    def _switch_view(self, index: int):
        self._view_stack.setCurrentIndex(index)
        self._table_btn.setChecked(index == 0)
        self._card_btn.setChecked(index == 1)
        if index == 1:
            self._populate_cards()

    # -- Data Loading --

    def load_data(self):
        """Load records from database."""
        offset = self._current_page * self._page_size
        records, total = self._record_service.search_records(
            query=self._query,
            visa_status=self._visa_status,
            educational_level=self._edu_level,
            year_level=self._year_level,
            include_inactive=self._include_inactive,
            offset=offset,
            limit=self._page_size,
        )
        self._current_records = records
        self._total_count = total

        # Batch-load document types for completeness
        record_ids = [r.id for r in records if r.id is not None]
        self._doc_types = self._record_service.get_document_types(record_ids)

        # Compute completeness
        from app.services.completeness import check_completeness
        self._completeness_cache = {}
        for r in records:
            types = self._doc_types.get(r.id, [])
            status, _ = check_completeness(r, len(types), types)
            self._completeness_cache[r.id] = status

        self._table_model.set_data(records, total, self._doc_types)
        self._update_pagination()

        if self._view_stack.currentIndex() == 1:
            self._populate_cards()

    def _populate_cards(self):
        """Build card widgets from current data."""
        # Clear existing cards
        while self._card_layout.count():
            item = self._card_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        cols = 3
        for c in range(cols):
            self._card_layout.setColumnStretch(c, 1)
        for i, record in enumerate(self._current_records):
            # Use cached profile picture path to avoid repeated file I/O
            if record.id not in self._pic_path_cache:
                self._pic_path_cache[record.id] = self._image_service.get_profile_picture_path(record.id)
            pic_path = self._pic_path_cache[record.id]
            completeness = self._completeness_cache.get(record.id, "")
            card = RecordCard(record, pic_path, completeness)
            card.clicked.connect(self.record_selected.emit)
            row = i // cols
            col = i % cols
            self._card_layout.addWidget(card, row, col)

        # Spacer at bottom
        spacer_row = (len(self._current_records) // cols) + 1 if self._current_records else 0
        self._card_layout.setRowStretch(spacer_row, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._view_stack.currentIndex() == 1:
            self._resize_timer.start()

    # -- Pagination --

    def _update_pagination(self):
        total_pages = max(1, (self._total_count + self._page_size - 1) // self._page_size)
        current = self._current_page + 1
        self._page_label.setText(f"Page {current} of {total_pages}")
        self._prev_btn.setEnabled(self._current_page > 0)
        self._next_btn.setEnabled(current < total_pages)
        self._record_count_label.setText(f"{self._total_count} records")

    def _prev_page(self):
        if self._current_page > 0:
            self._current_page -= 1
            self.load_data()

    def _next_page(self):
        total_pages = max(1, (self._total_count + self._page_size - 1) // self._page_size)
        if self._current_page + 1 < total_pages:
            self._current_page += 1
            self.load_data()

    def _on_page_size_changed(self):
        self._page_size = self._page_size_combo.currentData()
        self._current_page = 0
        self.load_data()

    # -- Search --

    def _on_search_changed(self, query, visa_status, edu_level, year_level, include_inactive):
        self._query = query
        self._visa_status = visa_status
        self._edu_level = edu_level
        self._year_level = year_level
        self._include_inactive = include_inactive
        self._current_page = 0

        # Also apply client-side instant filter on the proxy
        self._proxy_model.set_search_text(query)

        self.load_data()

    # -- Events --

    def _on_table_double_click(self, index):
        source_index = self._proxy_model.mapToSource(index)
        record = self._table_model.get_record(source_index.row())
        if record and record.id:
            self.record_selected.emit(record.id)
