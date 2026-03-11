from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QSizePolicy, QGraphicsDropShadowEffect,
)

from app.services.record_service import RecordService
from app.services.image_service import ImageService
from app.constants import DocumentType
from app.utils.logger import get_logger

logger = get_logger(__name__)

PANEL_WIDTH = 360
PLACEHOLDER_COLOR = "#E5E5EA"
ACCENT = "#007AFF"


# ─────────────────────────────────────────────
# Helper widgets
# ─────────────────────────────────────────────

def _section_title(text: str, parent: QWidget = None) -> QLabel:
    lbl = QLabel(text.upper(), parent)
    lbl.setStyleSheet(
        "font-weight: 700; color: #8E8E93; "
        "letter-spacing: 1px; padding-top: 4px;"
    )
    return lbl


def _divider(parent: QWidget = None) -> QFrame:
    line = QFrame(parent)
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet("background-color: #E5E5EA;")
    return line


def _field_row(label: str, value: str, parent: QWidget = None) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(6)
    lbl = QLabel(label, parent)
    lbl.setStyleSheet("color: #8E8E93; min-width: 110px;")
    lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
    val = QLabel(value or "—", parent)
    val.setStyleSheet("color: #1D1D1F;")
    val.setWordWrap(True)
    row.addWidget(lbl)
    row.addWidget(val, stretch=1)
    return row


def _format_date(raw: str) -> str:
    """Convert YYYY-MM-DD → MM/DD/YYYY."""
    if not raw:
        return "—"
    parts = raw.split("-")
    if len(parts) == 3:
        return f"{parts[1]}/{parts[2]}/{parts[0]}"
    return raw


def _circular_pixmap(path: str, size: int) -> QPixmap:
    src = QPixmap(path)
    if src.isNull():
        return QPixmap()
    src = src.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    x = (src.width() - size) // 2
    y = (src.height() - size) // 2
    cropped = src.copy(x, y, size, size)
    result = QPixmap(size, size)
    result.fill(Qt.transparent)
    p = QPainter(result)
    p.setRenderHint(QPainter.Antialiasing)
    path_obj = QPainterPath()
    path_obj.addEllipse(0, 0, size, size)
    p.setClipPath(path_obj)
    p.drawPixmap(0, 0, cropped)
    p.end()
    return result


# ─────────────────────────────────────────────
# Section Widgets
# ─────────────────────────────────────────────

class _ProfileSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Avatar + name side by side
        top = QHBoxLayout()
        top.setSpacing(14)

        self._avatar = QLabel(self)
        self._avatar.setFixedSize(80, 80)
        self._avatar.setAlignment(Qt.AlignCenter)
        self._avatar.setStyleSheet(
            f"background-color: {PLACEHOLDER_COLOR}; border-radius: 40px; "
            "color: #8E8E93;"
        )
        top.addWidget(self._avatar)

        name_col = QVBoxLayout()
        name_col.setSpacing(3)
        self._name_lbl = QLabel(self)
        self._name_lbl.setStyleSheet("font-weight: 700; color: #1D1D1F;")
        self._name_lbl.setWordWrap(True)
        self._passport_lbl = QLabel(self)
        self._passport_lbl.setStyleSheet("color: #8E8E93;")
        self._nationality_lbl = QLabel(self)
        self._nationality_lbl.setStyleSheet("color: #6E6E73;")
        name_col.addWidget(self._name_lbl)
        name_col.addWidget(self._passport_lbl)
        name_col.addWidget(self._nationality_lbl)
        name_col.addStretch()
        top.addLayout(name_col, stretch=1)
        layout.addLayout(top)

    def update(self, record, pic_path: str | None):
        self._name_lbl.setText(record.full_name)
        self._passport_lbl.setText(record.passport_number or "—")
        self._nationality_lbl.setText(record.country_of_citizenship or "—")

        if pic_path:
            pix = _circular_pixmap(pic_path, 80)
            if not pix.isNull():
                self._avatar.setPixmap(pix)
                self._avatar.setStyleSheet("border-radius: 40px;")
                return
        self._avatar.setText("?")
        self._avatar.setStyleSheet(
            f"background-color: {PLACEHOLDER_COLOR}; border-radius: 40px; "
            "color: #8E8E93;"
        )
        self._avatar.setPixmap(QPixmap())


class _IdentitySection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(_section_title("Identity", self))
        layout.addWidget(_divider(self))
        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(4)
        layout.addLayout(self._rows_layout)

    def update(self, record):
        # Clear
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()
        for label, value in [
            ("Date of Birth", _format_date(record.date_of_birth)),
            ("Sex", record.sex),
        ]:
            self._rows_layout.addLayout(_field_row(label, value, self))


class _VisaSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(_section_title("Visa", self))
        layout.addWidget(_divider(self))
        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(4)
        layout.addLayout(self._rows_layout)

    def update(self, record):
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        for label, value in [
            ("Status", record.visa_status),
            ("Category", record.visa_category),
            ("Grant Date", _format_date(record.visa_grant_date)),
            ("Validity", _format_date(record.visa_validity_date)),
        ]:
            self._rows_layout.addLayout(_field_row(label, value, self))


class _EducationSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(_section_title("Education", self))
        layout.addWidget(_divider(self))
        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(4)
        layout.addLayout(self._rows_layout)

    def update(self, record):
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        for label, value in [
            ("Status", record.enrollment_status),
            ("Course / Program", record.course_program),
            ("Education Level", record.educational_level),
            ("Year Level", record.year_level),
            ("Semester", record.semester),
            ("Start Date", _format_date(record.date_start_education)),
        ]:
            self._rows_layout.addLayout(_field_row(label, value, self))


class _DocumentSection(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(_section_title("Documents", self))
        layout.addWidget(_divider(self))
        self._rows_layout = QVBoxLayout()
        self._rows_layout.setSpacing(4)
        layout.addLayout(self._rows_layout)

    def update(self, uploaded_types: list[str]):
        while self._rows_layout.count():
            item = self._rows_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        uploaded_set = set(uploaded_types)
        for doc_type in DocumentType:
            row = QHBoxLayout()
            row.setSpacing(0)
            name_lbl = QLabel(doc_type.value, self)
            name_lbl.setStyleSheet("color: #1D1D1F;")
            row.addWidget(name_lbl, stretch=1)

            if doc_type.value in uploaded_set:
                status_lbl = QLabel("Available", self)
                status_lbl.setStyleSheet("color: #34C759; font-weight: 600;")
            else:
                status_lbl = QLabel("Missing", self)
                status_lbl.setStyleSheet("color: #FF3B30; font-weight: 600;")
            row.addWidget(status_lbl)
            self._rows_layout.addLayout(row)


# ─────────────────────────────────────────────
# PreviewPanel (Floating Overlay)
# ─────────────────────────────────────────────

class PreviewPanel(QWidget):
    """
    Floating panel that overlays the record list pane.

    Usage:
        panel = PreviewPanel(parent=content_area_widget)
        panel.show_record(record_id)
        panel.hide_panel()
    """

    closed = Signal()
    open_requested = Signal(int)  # emitted when user clicks "Open Record"

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("previewPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Drop shadow – strong enough to lift the panel above the list
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setOffset(-4, 0)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.setGraphicsEffect(shadow)

        self._record_service = RecordService()
        self._image_service = ImageService()
        self._current_record_id: int | None = None

        self.setStyleSheet("""
            #previewPanel {
                background-color: #FFFFFF;
                border-left: 1.5px solid #C8CBD3;
                border-radius: 0px;
            }
        """)

        self._setup_ui()
        self.hide()

        # Slide-in animation
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header bar ──
        header = QWidget()
        header.setFixedHeight(44)
        header.setStyleSheet("background-color: #EBEBF0; border-bottom: 1px solid #D1D1D6;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(6, 0, 10, 0)
        h_layout.setSpacing(4)

        # Back / close button on the left
        back_btn = QPushButton("‹ Back", header)
        back_btn.setFixedHeight(28)
        back_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                color: #007AFF; padding: 0 8px;
            }
            QPushButton:hover { color: #0051D5; }
        """)
        back_btn.clicked.connect(self.hide_panel)
        h_layout.addWidget(back_btn)

        self._header_lbl = QLabel("Record Preview", header)
        self._header_lbl.setStyleSheet("font-weight: 600; color: #1D1D1F;")
        self._header_lbl.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(self._header_lbl, stretch=1)

        # Open Record button on the right
        self._open_btn = QPushButton("Open →", header)
        self._open_btn.setFixedHeight(26)
        self._open_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF; color: white;
                border: none; border-radius: 5px;
                font-weight: 600; padding: 0 10px;
            }
            QPushButton:hover { background-color: #0062CC; }
            QPushButton:disabled { background-color: #C7C7CC; color: #FFFFFF; }
        """)
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._on_open_clicked)
        h_layout.addWidget(self._open_btn)

        outer.addWidget(header)

        # ── Scroll area ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background-color: #FFFFFF; border: none; }")
        outer.addWidget(scroll, stretch=1)

        content = QWidget()
        content.setStyleSheet("background-color: #FFFFFF;")
        scroll.setWidget(content)

        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(16, 16, 16, 24)
        self._content_layout.setSpacing(16)

        # ── Empty state ──
        self._empty_lbl = QLabel("Select a record to view details", content)
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #8E8E93; padding: 40px 0;")
        self._content_layout.addWidget(self._empty_lbl)

        # ── Sections (hidden until a record is loaded) ──
        self._section_container = QWidget(content)
        self._section_container.setStyleSheet("background-color: #FFFFFF;")
        sc_layout = QVBoxLayout(self._section_container)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.setSpacing(16)

        self._profile_sec = _ProfileSection(self._section_container)
        self._identity_sec = _IdentitySection(self._section_container)
        self._visa_sec = _VisaSection(self._section_container)
        self._education_sec = _EducationSection(self._section_container)
        self._document_sec = _DocumentSection(self._section_container)

        sc_layout.addWidget(self._profile_sec)
        sc_layout.addWidget(self._identity_sec)
        sc_layout.addWidget(self._visa_sec)
        sc_layout.addWidget(self._education_sec)
        sc_layout.addWidget(self._document_sec)
        sc_layout.addStretch()

        self._content_layout.addWidget(self._section_container)
        self._section_container.setVisible(False)

    # ── Public API ──────────────────────────────

    def show_record(self, record_id: int):
        """Load and display a record. Shows the panel if hidden."""
        if record_id == self._current_record_id and self.isVisible():
            return  # nothing changed

        self._current_record_id = record_id

        try:
            record = self._record_service.get_record(record_id)
            if not record:
                self._show_empty()
                return

            pic_path = self._image_service.get_profile_picture_path(record_id)
            doc_types = self._record_service.get_document_types([record_id])
            uploaded = doc_types.get(record_id, [])

            self._profile_sec.update(record, pic_path)
            self._identity_sec.update(record)
            self._visa_sec.update(record)
            self._education_sec.update(record)
            self._document_sec.update(uploaded)

            self._empty_lbl.setVisible(False)
            self._section_container.setVisible(True)
            self._open_btn.setEnabled(True)
        except Exception as e:
            logger.error("PreviewPanel failed to load record %s: %s", record_id, e)
            self._show_empty()

        if not self.isVisible():
            self._slide_in()

    def hide_panel(self, animate: bool = True):
        """Animate out then hide (or hide instantly)."""
        if animate:
            self._slide_out()
        else:
            self._anim.stop()
            self.hide()
            
        self._current_record_id = None
        self._open_btn.setEnabled(False)
        self.closed.emit()

    def _on_open_clicked(self):
        if self._current_record_id is not None:
            self.open_requested.emit(self._current_record_id)

    def update_geometry_for_parent(self):
        """Call this from the parent's resizeEvent to keep the panel pinned."""
        if not self.parent():
            return
        parent: QWidget = self.parent()
        ph = parent.height()
        x = parent.width() - PANEL_WIDTH
        self.setGeometry(x, 0, PANEL_WIDTH, ph)

    # ── Internals ───────────────────────────────

    def _show_empty(self):
        self._empty_lbl.setVisible(True)
        self._section_container.setVisible(False)
        self._open_btn.setEnabled(False)

    def _slide_in(self):
        parent: QWidget = self.parent()
        if not parent:
            self.show()
            return
        ph = parent.height()
        pw = parent.width()
        target = QRect(pw - PANEL_WIDTH, 0, PANEL_WIDTH, ph)
        start = QRect(pw, 0, PANEL_WIDTH, ph)
        self.setGeometry(start)
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(target)
        self._anim.start()

    def _slide_out(self):
        if not self.isVisible():
            self.hide()
            return
        parent: QWidget = self.parent()
        if not parent:
            self.hide()
            return
        ph = parent.height()
        pw = parent.width()
        start = self.geometry()
        end = QRect(pw, 0, PANEL_WIDTH, ph)
        self._anim.stop()
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.finished.connect(self._on_slide_out_done)
        self._anim.start()

    def _on_slide_out_done(self):
        self.hide()
        try:
            self._anim.finished.disconnect(self._on_slide_out_done)
        except RuntimeError:
            pass
