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
    QMessageBox,
)

from app.constants import DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS, ENROLLMENT_STATUSES
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
    double_clicked = Signal(int)

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
        avatar = QLabel(self)
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
                "background-color: #E5E7EB; border-radius: 20px; color: #9CA3AF; font-size: 18px; font-weight: 600;"
            )
        top.addWidget(avatar)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_label = QLabel(record.full_name, self)
        name_label.setStyleSheet("font-weight: 600; font-size: 16px; color: #1F2933;")
        name_label.setWordWrap(True)
        name_col.addWidget(name_label)

        passport_label = QLabel(record.passport_number, self)
        passport_label.setStyleSheet("font-size: 14px; color: #6B7280;")
        name_col.addWidget(passport_label)
        top.addLayout(name_col, stretch=1)

        # Completeness badge
        if completeness == "complete":
            badge = QLabel("Complete Docs", self)
            badge.setStyleSheet(
                "background-color: #10B981; color: white; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
            badge.setFixedHeight(20)
            top.addWidget(badge, alignment=Qt.AlignTop)
        elif completeness == "missing_fields":
            badge = QLabel("Missing Fields", self)
            badge.setStyleSheet(
                "background-color: #F59E0B; color: white; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
            badge.setFixedHeight(20)
            top.addWidget(badge, alignment=Qt.AlignTop)
        elif completeness == "incomplete_documents":
            badge = QLabel("Incomplete Docs", self)
            badge.setStyleSheet(
                "background-color: #F59E0B; color: white; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
            badge.setFixedHeight(20)
            top.addWidget(badge, alignment=Qt.AlignTop)
        elif completeness == "no_documents":
            badge = QLabel("No Docs", self)
            badge.setStyleSheet(
                "background-color: #EF4444; color: white; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
            badge.setFixedHeight(20)
            top.addWidget(badge, alignment=Qt.AlignTop)

        layout.addLayout(top)

        # Divider
        div = QFrame(self)
        div.setFrameShape(QFrame.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")
        layout.addWidget(div)

        # Details
        visa = record.visa_category or ""
        course = record.course_program or ""
        details = [
            ("Visa", visa[:25] + "..." if len(visa) > 25 else visa),
            ("Status", record.visa_status),
            ("Course", course[:20] + "..." if len(course) > 20 else course),
            ("Year", record.year_level),
        ]
        for label_text, value in details:
            if value:
                row = QHBoxLayout()
                row.setSpacing(6)
                lbl = QLabel(f"{label_text}:", self)
                lbl.setStyleSheet("font-size: 13px; color: #9CA3AF; min-width: 40px;")
                row.addWidget(lbl)
                val = QLabel(value, self)
                val.setStyleSheet("font-size: 13px; color: #1F2933;")
                val.setWordWrap(True)
                row.addWidget(val, stretch=1)
                layout.addLayout(row)

    def mousePressEvent(self, event):
        if self._record_id is not None:
            self.clicked.emit(self._record_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._record_id is not None:
            self.double_clicked.emit(self._record_id)
        super().mouseDoubleClickEvent(event)


class RecordListPage(QWidget):
    """Main record list with table and card views."""

    record_preview_requested = Signal(int)
    record_open_requested = Signal(int)
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
        self._active_status = "active"
        self._current_records: list[WalkInRecord] = []
        self._doc_counts: dict[int, int] = {}
        self._pic_path_cache: dict[int, str | None] = {}
        self._completeness_cache: dict[int, str] = {}

        # Debounce timer for card rebuild on resize
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(300)
        self._resize_timer.timeout.connect(self._populate_cards)

        # Debounce timer to prevent preview panel flashing on double-click
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        # We will set the interval dynamically based on system double-click speed
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        dbl_click_ms = app.doubleClickInterval() if app else 500
        self._click_timer.setInterval(dbl_click_ms)
        self._click_timer.timeout.connect(self._emit_preview_delayed)
        self._pending_preview_id = None

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
        self._table_btn.setChecked(False)
        self._table_btn.setFixedHeight(36)
        self._table_btn.clicked.connect(lambda: self._switch_view(0))

        self._card_btn = QPushButton("Cards")
        self._card_btn.setCheckable(True)
        self._card_btn.setChecked(True)
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
        self._table_view.setFocusPolicy(Qt.NoFocus)
        self._table_view.setModel(self._proxy_model)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table_view.setSortingEnabled(True)
        self._table_view.verticalHeader().setVisible(False)
        self._table_view.setShowGrid(False)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table_view.horizontalHeader().setDefaultSectionSize(140)
        self._table_view.horizontalHeader().setMinimumSectionSize(80)
        self._table_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        # A5 — 40px rows match macOS system table proportions
        self._table_view.verticalHeader().setDefaultSectionSize(40)
        self._table_view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self._table_view.clicked.connect(self._on_table_clicked)
        self._table_view.doubleClicked.connect(self._on_table_double_click)

        # Set Document column width
        self._table_view.horizontalHeader().resizeSection(0, 100)
        self._table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

        # A2 — empty-state overlay (shown when 0 rows match)
        self._empty_label = QLabel("No records found.\nTry adjusting your search or filter.", self._table_view)
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: #9CA3AF; font-size: 15px; padding: 32px;"
        )
        self._empty_label.setVisible(False)

        self._view_stack.addWidget(self._table_view)

        # Connect selection model so batch toolbar can react
        self._table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )

        # --- Card View ---
        self._card_scroll = QScrollArea()
        self._card_scroll.setWidgetResizable(True)
        self._card_scroll.setFrameShape(QFrame.NoFrame)
        self._card_container = QWidget(self._card_scroll)
        self._card_layout = QGridLayout(self._card_container)
        self._card_layout.setSpacing(12)
        self._card_layout.setContentsMargins(0, 0, 0, 0)
        self._card_scroll.setWidget(self._card_container)
        self._view_stack.addWidget(self._card_scroll)

        # --- Empty State ---
        self._empty_state = QWidget()
        empty_layout = QVBoxLayout(self._empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(12)

        empty_icon = QLabel("📋", self._empty_state)
        empty_icon.setStyleSheet("font-size: 36px; background: transparent;")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_icon)

        empty_title = QLabel("No records found", self._empty_state)
        empty_title.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #1F2933; background: transparent;"
        )
        empty_title.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel(
            "Try adjusting your search or filters, or add a new record.",
            self._empty_state,
        )
        empty_desc.setStyleSheet("font-size: 14px; color: #6B7280; background: transparent;")
        empty_desc.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_desc)

        empty_add_btn = QPushButton("+ Add Record", self._empty_state)
        empty_add_btn.setObjectName("primaryButton")
        empty_add_btn.setFixedHeight(38)
        empty_add_btn.setFixedWidth(160)
        empty_add_btn.clicked.connect(self.add_record_requested.emit)
        empty_layout.addWidget(empty_add_btn, alignment=Qt.AlignCenter)

        self._view_stack.addWidget(self._empty_state)  # index 2

        layout.addWidget(self._view_stack, stretch=1)

        # ── Batch Action Toolbar (hidden until 2+ rows selected) ──
        self._batch_toolbar = QFrame(self)
        self._batch_toolbar.setObjectName("batchToolbar")
        self._batch_toolbar.setStyleSheet(
            f"""#batchToolbar {{
                background-color: {Colors.ACCENT};
                border-radius: 8px;
                padding: 2px 6px;
            }}"""
        )
        self._batch_toolbar.setVisible(False)
        batch_layout = QHBoxLayout(self._batch_toolbar)
        batch_layout.setContentsMargins(12, 6, 12, 6)
        batch_layout.setSpacing(10)

        self._batch_count_label = QLabel("", self._batch_toolbar)
        self._batch_count_label.setStyleSheet("color: white; font-size: 13px; font-weight: 600;")
        batch_layout.addWidget(self._batch_count_label)

        batch_layout.addStretch()

        # ── Archive / Restore button ──
        self._batch_archive_btn = QPushButton("Archive", self._batch_toolbar)
        self._batch_archive_btn.setFixedHeight(28)
        self._batch_archive_btn.setStyleSheet(
            "background: #DC2626; color: white; font-weight: 600;"
            "border-radius: 4px; padding: 0 12px; border: none;"
        )
        self._batch_archive_btn.setToolTip("Archive selected records (deactivate)")
        self._batch_archive_btn.clicked.connect(self._batch_archive)
        batch_layout.addWidget(self._batch_archive_btn)

        self._batch_restore_btn = QPushButton("Restore", self._batch_toolbar)
        self._batch_restore_btn.setFixedHeight(28)
        self._batch_restore_btn.setStyleSheet(
            "background: #10B981; color: white; font-weight: 600;"
            "border-radius: 4px; padding: 0 12px; border: none;"
        )
        self._batch_restore_btn.setToolTip("Restore selected archived records")
        self._batch_restore_btn.clicked.connect(self._batch_restore)
        batch_layout.addWidget(self._batch_restore_btn)

        # Separator
        self._batch_separator = QFrame(self._batch_toolbar)
        self._batch_separator.setFixedWidth(1)
        self._batch_separator.setFixedHeight(20)
        self._batch_separator.setStyleSheet("background-color: rgba(255,255,255,0.3);")
        batch_layout.addWidget(self._batch_separator)

        # ── Enrollment status update ──
        self._batch_status_label = QLabel("Set status:", self._batch_toolbar)
        self._batch_status_label.setStyleSheet("color: white; font-size: 13px;")
        batch_layout.addWidget(self._batch_status_label)

        self._batch_status_combo = QComboBox(self._batch_toolbar)
        self._batch_status_combo.setFixedHeight(28)
        from app.constants import ENROLLMENT_STATUSES
        for s in ENROLLMENT_STATUSES:
            self._batch_status_combo.addItem(s)
        batch_layout.addWidget(self._batch_status_combo)

        self._batch_apply_btn = QPushButton("Apply", self._batch_toolbar)
        self._batch_apply_btn.setFixedHeight(28)
        self._batch_apply_btn.setStyleSheet(
            "background: white; color: #4F8EF7; font-weight: 600;"
            "border-radius: 4px; padding: 0 12px;"
        )
        self._batch_apply_btn.clicked.connect(self._apply_batch_update)
        batch_layout.addWidget(self._batch_apply_btn)

        cancel_batch_btn = QPushButton("✕", self._batch_toolbar)
        cancel_batch_btn.setFixedHeight(28)
        cancel_batch_btn.setFixedWidth(28)
        cancel_batch_btn.setStyleSheet(
            "background: rgba(255,255,255,0.2); color: white; border-radius: 4px;"
        )
        cancel_batch_btn.setToolTip("Clear selection")
        cancel_batch_btn.clicked.connect(self._table_view.clearSelection)
        batch_layout.addWidget(cancel_batch_btn)

        layout.addWidget(self._batch_toolbar)

        # Pagination
        pag = QHBoxLayout()
        pag.setSpacing(8)

        self._record_count_label = QLabel("0 records", self)
        self._record_count_label.setObjectName("subtitleLabel")
        pag.addWidget(self._record_count_label)

        pag.addStretch()

        self._prev_btn = QPushButton("Previous", self)
        self._prev_btn.setFixedHeight(34)
        self._prev_btn.clicked.connect(self._prev_page)
        pag.addWidget(self._prev_btn)

        self._page_label = QLabel("Page 1", self)
        self._page_label.setStyleSheet("font-size: 14px; color: #6B7280; padding: 0 8px;")
        pag.addWidget(self._page_label)

        self._next_btn = QPushButton("Next", self)
        self._next_btn.setFixedHeight(34)
        self._next_btn.clicked.connect(self._next_page)
        pag.addWidget(self._next_btn)

        pag.addWidget(QLabel("Per page:", self))
        self._page_size_combo = QComboBox(self)
        for ps in PAGE_SIZE_OPTIONS:
            self._page_size_combo.addItem(str(ps), ps)
        self._page_size_combo.setCurrentText(str(self._page_size))
        self._page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)
        pag.addWidget(self._page_size_combo)

        layout.addLayout(pag)

        # Default to Card view
        self._view_stack.setCurrentIndex(1)

    # -- Read-Only Mode --

    def set_read_only(self, enabled: bool):
        """Show or hide the add button based on read-only mode."""
        self._add_btn.setVisible(not enabled)
        self._read_only = enabled

    # -- Batch Selection --

    def _get_selected_record_ids(self) -> list[int]:
        """Extract record IDs from current table selection."""
        selected_rows = self._table_view.selectionModel().selectedRows()
        record_ids = []
        for index in selected_rows:
            source_index = self._proxy_model.mapToSource(index)
            record = self._table_model.get_record(source_index.row())
            if record and record.id:
                record_ids.append(record.id)
        return record_ids

    def _on_selection_changed(self):
        """Show/hide the batch toolbar based on how many rows are selected."""
        selected_rows = self._table_view.selectionModel().selectedRows()
        count = len(selected_rows)
        if count > 1:
            self._batch_count_label.setText(f"{count} records selected")
            self._batch_toolbar.setVisible(True)
            # Show context-appropriate buttons
            viewing_archived = self._active_status == "archived"
            self._batch_archive_btn.setVisible(not viewing_archived)
            self._batch_restore_btn.setVisible(viewing_archived)
            # Hide enrollment status controls when viewing archived
            self._batch_status_combo.setVisible(not viewing_archived)
            self._batch_status_label.setVisible(not viewing_archived)
            self._batch_apply_btn.setVisible(not viewing_archived)
            self._batch_separator.setVisible(not viewing_archived)
        else:
            self._batch_toolbar.setVisible(False)

    def _apply_batch_update(self):
        """Apply enrollment status to all selected records."""
        record_ids = self._get_selected_record_ids()
        if not record_ids:
            return

        new_status = self._batch_status_combo.currentText()
        reply = QMessageBox.question(
            self,
            "Confirm Batch Update",
            f"Update enrollment status to '{new_status}' for {len(record_ids)} record(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            self._record_service.batch_update_enrollment_status(record_ids, new_status)
            self._table_view.clearSelection()
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "Batch Update Failed", str(e))

    def _batch_archive(self):
        """Archive (deactivate) all selected records."""
        record_ids = self._get_selected_record_ids()
        if not record_ids:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Batch Archive",
            f"Archive {len(record_ids)} record(s)?\n\n"
            "Archived records can be restored later from the Archived view.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            count = self._record_service.batch_archive(record_ids)
            self._table_view.clearSelection()
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "Batch Archive Failed", str(e))

    def _batch_restore(self):
        """Restore all selected archived records."""
        record_ids = self._get_selected_record_ids()
        if not record_ids:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Batch Restore",
            f"Restore {len(record_ids)} archived record(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            count = self._record_service.batch_restore(record_ids)
            self._table_view.clearSelection()
            self.load_data()
        except Exception as e:
            QMessageBox.warning(self, "Batch Restore Failed", str(e))

    # -- View Toggle --

    def _switch_view(self, index: int):
        self._view_stack.setCurrentIndex(index)
        self._table_btn.setChecked(index == 0)
        self._card_btn.setChecked(index == 1)
        if index == 1:
            self._populate_cards()

    # -- Data Loading --

    def apply_filter(self, filter_type: str):
        """Apply a dashboard filter and reload data."""
        # Reset search bar
        self._search_bar.clear_all()
        self._query = ""
        self._visa_status = ""
        self._edu_level = ""
        self._year_level = ""
        self._active_status = "active"
        self._current_page = 0

        if filter_type == "inactive":
            self._active_status = "archived"
        elif filter_type in ("missing_docs", "expired_visa", "expiring_visa", "active"):
            # These filters are handled via special query in load_data
            pass

        self._active_filter = filter_type
        self.load_data()

    def load_data(self):
        """Load records from database."""
        offset = self._current_page * self._page_size

        # Check for special dashboard filters
        active_filter = getattr(self, "_active_filter", "")

        if active_filter in ("expired_visa", "expiring_visa", "missing_docs"):
            from app.services.dashboard_service import DashboardService
            ds = DashboardService()
            if active_filter == "expired_visa":
                ids = ds.get_expired_visa_ids()
            elif active_filter == "expiring_visa":
                ids = ds.get_expiring_visa_ids()
            else:
                ids = self._get_missing_docs_ids()

            # Filter records natively by IDs
            records, total = self._record_service.search_records(
                active_status=self._active_status,
                record_ids=ids,
                offset=offset,
                limit=self._page_size,
            )
        else:
            records, total = self._record_service.search_records(
                query=self._query,
                visa_status=self._visa_status,
                educational_level=self._edu_level,
                year_level=self._year_level,
                active_status=self._active_status,
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

        # Show empty state or active view
        if total == 0:
            self._view_stack.setCurrentIndex(2)  # empty state
        elif self._view_stack.currentIndex() == 2:
            self._view_stack.setCurrentIndex(0)  # back to table

        if self._view_stack.currentIndex() == 1:
            self._populate_cards()

    def _get_missing_docs_ids(self) -> list[int]:
        """Get IDs of active records missing required documents."""
        from app.database import get_connection
        from app.constants import DocumentType
        required_count = len(DocumentType)
        conn = get_connection()
        rows = conn.execute(
            f"""SELECT w.id FROM walkin_records w
               WHERE w.is_active = 1
               AND (SELECT COUNT(DISTINCT d.document_type)
                    FROM documents d WHERE d.record_id = w.id) < ?""",
            (required_count,),
        ).fetchall()
        return [r["id"] for r in rows]

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
            card.clicked.connect(self._on_card_clicked)
            card.double_clicked.connect(self._on_card_double_clicked)
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
        self._page_size = self._page_size_combo.currentData() or DEFAULT_PAGE_SIZE
        self._current_page = 0
        self.load_data()

    # -- Search --

    def _on_search_changed(self, query, visa_status, edu_level, year_level, active_status):
        self._active_filter = ""
        self._query = query
        self._visa_status = visa_status
        self._edu_level = edu_level
        self._year_level = year_level
        self._active_status = active_status
        self._current_page = 0

        # Also apply client-side instant filter on the proxy
        self._proxy_model.set_search_text(query)
        self._proxy_model.set_active_status(active_status)

        self.load_data()

    # -- Events --

    def _emit_preview_delayed(self):
        if self._pending_preview_id is not None:
            self.record_preview_requested.emit(self._pending_preview_id)
            self._pending_preview_id = None

    def _on_card_clicked(self, record_id: int):
        self._pending_preview_id = record_id
        self._click_timer.start()

    def _on_card_double_clicked(self, record_id: int):
        self._click_timer.stop()
        self.record_open_requested.emit(record_id)

    def _on_table_clicked(self, index):
        source_index = self._proxy_model.mapToSource(index)
        record = self._table_model.get_record(source_index.row())
        if record and record.id:
            self._pending_preview_id = record.id
            self._click_timer.start()

    def _on_table_double_click(self, index):
        self._click_timer.stop()
        source_index = self._proxy_model.mapToSource(index)
        record = self._table_model.get_record(source_index.row())
        if record and record.id:
            self.record_open_requested.emit(record.id)
