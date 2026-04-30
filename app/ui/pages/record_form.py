"""
Add / Edit record form with full validation, autosave drafts, and unsaved changes guard.
"""
from PySide6.QtCore import Qt, Signal, QTimer, QDate, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QTextEdit, QLabel, QPushButton, QScrollArea,
    QFrame, QGroupBox, QMessageBox, QCompleter, QDateEdit,
    QSizePolicy,
)

from app.constants import (
    Sex, VisaStatus, EducationalLevel, Semester,
    VISA_CATEGORIES, YEAR_LEVELS, COUNTRIES, SUFFIX_NAMES, PH_REGIONS,
)
from app.models import WalkInRecord
from app.services.record_service import RecordService
from app.services.draft_service import DraftService
from app.utils.validators import (
    validate_required, validate_date_required, validate_date, validate_passport,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


AUTOSAVE_INTERVAL_MS = 30_000  # 30 seconds


class ClearableDateEdit(QDateEdit):
    """Date field with free-form typing, placeholder, and calendar popup.

    Bypasses QDateEdit's section-by-section editing so the user can
    simply type a date like '02/10/2004'.  The text is parsed into a
    real QDate on focus-out.  Backspace / Delete clear the field.
    The calendar popup dropdown still works normally.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_empty = True
        self.lineEdit().setPlaceholderText("MM/DD/YYYY")
        self.dateChanged.connect(self._on_date_changed)

    # ── helpers ──

    def _on_date_changed(self):
        self._is_empty = (self.date() == self.minimumDate())
        self._sync_placeholder()

    def _set_line_text(self, text, cursor):
        """Set line-edit text without triggering QDateEdit validation."""
        le = self.lineEdit()
        le.blockSignals(True)
        le.setText(text)
        le.setCursorPosition(cursor)
        le.blockSignals(False)

    def _sync_placeholder(self):
        """Clear line-edit text when empty so the native placeholder shows."""
        if self._is_empty and not self.hasFocus():
            self._set_line_text("", 0)

    # ── focus ──

    def focusInEvent(self, event):
        # Skip QDateEdit's focusInEvent (which selects a section)
        QWidget.focusInEvent(self, event)
        if self._is_empty:
            self._set_line_text("", 0)

    def focusOutEvent(self, event):
        self._parse_and_apply()
        super().focusOutEvent(event)
        self._sync_placeholder()

    # ── keyboard — bypass section editing, type freely ──

    def keyPressEvent(self, event: QKeyEvent):
        le = self.lineEdit()
        key = event.key()

        # Backspace
        if key == Qt.Key_Backspace:
            if le.hasSelectedText():
                s = le.selectionStart()
                e = s + len(le.selectedText())
                self._set_line_text(le.text()[:s] + le.text()[e:], s)
            elif le.cursorPosition() > 0:
                p = le.cursorPosition()
                self._set_line_text(le.text()[:p-1] + le.text()[p:], p - 1)
            # If now empty, reset
            if not le.text().strip():
                self._is_empty = True
            return

        # Delete
        if key == Qt.Key_Delete:
            if le.hasSelectedText():
                s = le.selectionStart()
                e = s + len(le.selectedText())
                self._set_line_text(le.text()[:s] + le.text()[e:], s)
            else:
                p = le.cursorPosition()
                t = le.text()
                if p < len(t):
                    self._set_line_text(t[:p] + t[p+1:], p)
            if not le.text().strip():
                self._is_empty = True
            return

        # Printable characters (digits, slashes, etc.)
        if event.text() and event.text().isprintable():
            p = le.cursorPosition()
            t = le.text()
            if le.hasSelectedText():
                s = le.selectionStart()
                e = s + len(le.selectedText())
                new = t[:s] + event.text() + t[e:]
                self._set_line_text(new, s + len(event.text()))
            else:
                self._set_line_text(t[:p] + event.text() + t[p:], p + len(event.text()))
            self._is_empty = False
            return

        # Navigation keys
        if key == Qt.Key_Left:
            le.setCursorPosition(max(0, le.cursorPosition() - 1))
            return
        if key == Qt.Key_Right:
            le.setCursorPosition(min(len(le.text()), le.cursorPosition() + 1))
            return
        if key == Qt.Key_Home:
            le.setCursorPosition(0)
            return
        if key == Qt.Key_End:
            le.setCursorPosition(len(le.text()))
            return

        # Select-all
        if key == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            le.selectAll()
            return

        # Everything else (Tab, Escape, etc.) → default QWidget handling
        QWidget.keyPressEvent(self, event)

    # ── parse typed text into a QDate ──

    def _parse_and_apply(self):
        """Try to parse the line-edit text as a date and apply it."""
        text = self.lineEdit().text().strip()
        if not text:
            self._is_empty = True
            self.setDate(self.minimumDate())
            return

        # Try MM/dd/yyyy first, then common alternatives
        for fmt in ("MM/dd/yyyy", "M/d/yyyy", "MM-dd-yyyy", "M-d-yyyy"):
            date = QDate.fromString(text, fmt)
            if date.isValid() and date > self.minimumDate():
                self._is_empty = False
                self.setDate(date)
                return

        # Invalid text → reset to empty
        self._is_empty = True
        self.setDate(self.minimumDate())

    # ── show ──

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._sync_placeholder)


class RecordForm(QWidget):
    """Form for creating or editing a walk-in record."""

    saved = Signal(int)      # Emits record ID on save
    cancelled = Signal()

    def __init__(self, record_id: int | None = None, parent=None):
        super().__init__(parent)
        self._record_id = record_id
        self._record_service = RecordService()
        self._draft_service = DraftService()
        self._fields: dict[str, QWidget] = {}
        self._error_labels: dict[str, QLabel] = {}
        self._initial_values: dict[str, str] = {}
        self._setup_ui()

        if record_id:
            self._load_record()

        # Snapshot initial values for dirty tracking
        self._snapshot_initial()

        # Check for existing draft and offer restore
        self._check_draft()

        # Autosave timer
        self._autosave_timer = QTimer()
        self._autosave_timer.setInterval(AUTOSAVE_INTERVAL_MS)
        self._autosave_timer.timeout.connect(self._autosave_draft)
        self._autosave_timer.start()


    # ── Draft key ──

    @property
    def _draft_key(self) -> str:
        if self._record_id:
            return f"edit_{self._record_id}"
        return "new"

    # ── Dirty tracking ──

    def _snapshot_initial(self):
        """Capture current field values as the baseline for dirty checking."""
        self._initial_values = {key: self._get_value(key) for key in self._fields}

    def has_unsaved_changes(self) -> bool:
        """Return True if any field value differs from the initial snapshot."""
        for key in self._fields:
            if self._get_value(key) != self._initial_values.get(key, ""):
                return True
        return False

    def confirm_discard(self) -> bool:
        """Show a Save/Discard/Cancel dialog. Returns True if user chose to proceed (discard)."""
        if not self.has_unsaved_changes():
            return True

        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "You have unsaved changes. Do you want to discard them?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if reply == QMessageBox.Save:
            return self._on_save()  # Only proceed if save succeeded
        elif reply == QMessageBox.Discard:
            self._delete_draft()
            return True
        return False  # Cancel

    # ── Autosave Drafts ──

    def _check_draft(self):
        """If a draft exists, prompt user to restore or discard."""
        draft = self._draft_service.load_draft(self._draft_key)
        if draft:
            reply = QMessageBox.question(
                self, "Draft Found",
                "An autosaved draft was found for this form.\n"
                "Would you like to restore it?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self._restore_draft(draft)
            else:
                self._draft_service.delete_draft(self._draft_key)

    def _restore_draft(self, draft: dict):
        """Populate form fields from a draft dictionary."""
        for key, value in draft.items():
            if key in self._fields:
                self._set_value(key, value)

    def _autosave_draft(self):
        """Save current form data as a draft if there are changes."""
        if not self.has_unsaved_changes():
            return
        data = {key: self._get_value(key) for key in self._fields}
        self._draft_service.save_draft(self._draft_key, data)

    def _delete_draft(self):
        """Remove the draft for this form."""
        self._draft_service.delete_draft(self._draft_key)

    # ── UI Setup ──

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title_text = "Edit Record" if self._record_id else "Add New Record"
        title = QLabel(title_text, self)
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.setFixedHeight(38)
        cancel_btn.clicked.connect(self._on_cancel)
        header.addWidget(cancel_btn)

        save_btn = QPushButton("Save Record", self)
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(38)
        save_btn.clicked.connect(self._on_save)
        header.addWidget(save_btn)

        outer.addLayout(header)

        # Scrollable form
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        form_widget = QWidget(scroll)
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(0, 0, 12, 0)

        # Section: Identity
        form_layout.addWidget(self._create_section("Identity", [
            ("last_name", "Last Name *", "line"),
            ("first_name", "First Name *", "line"),
            ("middle_name", "Middle Name", "line"),
            ("suffix_name", "Suffix", "combo", SUFFIX_NAMES),
            ("sex", "Sex *", "combo", [s.value for s in Sex]),
            ("date_of_birth", "Date of Birth *", "date"),
            ("passport_number", "Passport Number *", "line"),
            ("country_of_citizenship", "Country of Citizenship *", "combo", COUNTRIES),
        ]))

        # Section: Philippine Residential Address
        form_layout.addWidget(self._create_section("Philippine Residential Address", [
            ("street", "Street", "line"),
            ("barangay", "Barangay", "line"),
            ("city_municipality", "City / Municipality", "line"),
            ("province", "Province", "line"),
            ("region", "Region", "combo", PH_REGIONS),
        ]))

        # Section: Academic & Residency
        form_layout.addWidget(self._create_section("Academic & Residency Information", [
            ("date_of_arrival", "Date of Arrival", "date"),
            ("date_start_education", "Date of Start of Education", "date"),
            ("educational_level", "Educational Level", "combo", [el.value for el in EducationalLevel]),
            ("course_program", "Course / Program", "line"),
            ("year_level", "Year Level", "combo", YEAR_LEVELS),
            ("semester", "Semester", "combo", [s.value for s in Semester]),
            ("enrollment_status", "Remarks", "combo", ["Dropped", "Enrolled"]),
        ]))

        # Section: Visa Information
        form_layout.addWidget(self._create_section("Visa Information", [
            ("visa_category", "Visa Category", "combo", VISA_CATEGORIES),
            ("visa_grant_date", "Visa Grant Date", "date"),
            ("visa_validity_date", "Visa Validity Date", "date"),
            ("visa_status", "Status", "combo", [vs.value for vs in VisaStatus]),
            ("remarks", "Comments", "text"),
        ]))

        form_layout.addStretch()
        scroll.setWidget(form_widget)
        outer.addWidget(scroll, stretch=1)

    def _create_section(self, title: str, fields: list) -> QGroupBox:
        """Create a form section group box with clean alignment."""
        group = QGroupBox(title, self)
        layout = QFormLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        layout.setRowWrapPolicy(QFormLayout.DontWrapRows)

        for field_def in fields:
            key = field_def[0]
            label = field_def[1]
            field_type = field_def[2]

            # Create the input widget
            if field_type == "line":
                widget = QLineEdit(self)
                widget.setFixedHeight(38)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            elif field_type == "date":
                widget = ClearableDateEdit(self)
                widget.setCalendarPopup(True)
                widget.setDisplayFormat("MM/dd/yyyy")
                widget.setMinimumDate(QDate(1900, 1, 1))
                widget.setDate(QDate(1900, 1, 1))  # set to minimum so placeholder shows
                widget.setFixedHeight(38)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            elif field_type == "combo":
                options = field_def[3] if len(field_def) > 3 else []
                widget = QComboBox(self)
                widget.setEditable(True)
                widget.setInsertPolicy(QComboBox.NoInsert)
                widget.addItem("", "")  # Empty default
                for opt in options:
                    widget.addItem(opt, opt)
                # Enable substring filtering
                completer = widget.completer()
                completer.setCompletionMode(QCompleter.PopupCompletion)
                completer.setFilterMode(Qt.MatchContains)
                completer.setCaseSensitivity(Qt.CaseInsensitive)
                widget.setFixedHeight(38)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            elif field_type == "text":
                widget = QTextEdit(self)
                widget.setFixedHeight(100)
            else:
                widget = QLineEdit(self)
                widget.setFixedHeight(38)
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            self._fields[key] = widget

            # Error label
            err = QLabel(parent=self)
            err.setObjectName("errorLabel")
            err.setVisible(False)
            self._error_labels[key] = err

            # Wrap widget + error in a vertical layout
            wrapper = QVBoxLayout()
            wrapper.setSpacing(2)
            wrapper.setContentsMargins(0, 0, 0, 0)
            wrapper.addWidget(widget)
            wrapper.addWidget(err)

            lbl = QLabel(label, self)
            lbl.setObjectName("fieldLabel")
            lbl.setFixedWidth(260)
            layout.addRow(lbl, wrapper)

        group.setLayout(layout)
        return group

    # ── Field accessors ──

    def _get_value(self, key: str) -> str:
        """Get value from a field widget."""
        widget = self._fields.get(key)
        if isinstance(widget, QDateEdit):
            # Flush any typed-but-uncommitted text into the QDate value
            if isinstance(widget, ClearableDateEdit):
                widget._parse_and_apply()
            # Return empty string if date is at the special minimum value
            if widget.date() == widget.minimumDate():
                return ""
            return widget.date().toString("yyyy-MM-dd")
        elif isinstance(widget, QLineEdit):
            return widget.text().strip()
        elif isinstance(widget, QComboBox):
            # For editable combos, match typed text to an item
            if widget.isEditable():
                text = widget.currentText().strip()
                idx = widget.findText(text, Qt.MatchFixedString)
                if idx >= 0:
                    return widget.itemData(idx) or ""
                return ""  # typed text doesn't match any option
            return widget.currentData() or ""
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText().strip()
        return ""

    def _set_value(self, key: str, value: str):
        """Set value on a field widget."""
        widget = self._fields.get(key)
        if isinstance(widget, QDateEdit):
            if value:
                date = QDate.fromString(value, "yyyy-MM-dd")
                if date.isValid():
                    widget.setDate(date)
                    # Update line-edit text for ClearableDateEdit
                    if isinstance(widget, ClearableDateEdit):
                        widget._is_empty = False
                        widget._set_line_text(date.toString("MM/dd/yyyy"), 0)
                else:
                    widget.setDate(widget.minimumDate())
                    if isinstance(widget, ClearableDateEdit):
                        widget._is_empty = True
            else:
                widget.setDate(widget.minimumDate())
                if isinstance(widget, ClearableDateEdit):
                    widget._is_empty = True
        elif isinstance(widget, QLineEdit):
            widget.setText(value)
        elif isinstance(widget, QComboBox):
            idx = widget.findData(value)
            if idx >= 0:
                widget.setCurrentIndex(idx)
            elif widget.isEditable():
                widget.setCurrentText(value)
        elif isinstance(widget, QTextEdit):
            widget.setPlainText(value)

    # ── Validation ──

    def _show_error(self, key: str, message: str):
        """Show inline error for a field."""
        lbl = self._error_labels.get(key)
        if lbl:
            lbl.setText(message)
            lbl.setVisible(True)

    def _clear_errors(self):
        """Clear all error labels."""
        for lbl in self._error_labels.values():
            lbl.setVisible(False)

    def _validate(self) -> bool:
        """Validate all fields. Returns True if valid."""
        self._clear_errors()
        valid = True

        # Required fields
        required = [
            ("last_name", "Last Name"),
            ("first_name", "First Name"),
            ("sex", "Sex"),
            ("passport_number", "Passport Number"),
            ("country_of_citizenship", "Country of Citizenship"),
        ]
        for key, name in required:
            err = validate_required(self._get_value(key), name)
            if err:
                self._show_error(key, err)
                valid = False

        # Date of birth (required)
        dob = self._get_value("date_of_birth")
        err = validate_date_required(dob, "Date of Birth")
        if err:
            self._show_error("date_of_birth", err)
            valid = False

        # Passport
        err = validate_passport(self._get_value("passport_number"))
        if err:
            self._show_error("passport_number", err)
            valid = False

        # Optional dates
        for key, name in [
            ("date_of_arrival", "Date of Arrival"),
            ("date_start_education", "Date of Start of Education"),
            ("visa_grant_date", "Visa Grant Date"),
            ("visa_validity_date", "Visa Validity Date"),
        ]:
            val = self._get_value(key)
            if val:
                err = validate_date(val, name)
                if err:
                    self._show_error(key, err)
                    valid = False

        return valid

    # ── Build / Load ──

    def _build_record(self) -> WalkInRecord:
        """Build a WalkInRecord from form values."""
        return WalkInRecord(
            last_name=self._get_value("last_name"),
            first_name=self._get_value("first_name"),
            middle_name=self._get_value("middle_name"),
            suffix_name=self._get_value("suffix_name"),
            sex=self._get_value("sex"),
            date_of_birth=self._get_value("date_of_birth"),
            passport_number=self._get_value("passport_number"),
            country_of_citizenship=self._get_value("country_of_citizenship"),
            street=self._get_value("street"),
            barangay=self._get_value("barangay"),
            city_municipality=self._get_value("city_municipality"),
            province=self._get_value("province"),
            region=self._get_value("region"),
            date_of_arrival=self._get_value("date_of_arrival"),
            date_start_education=self._get_value("date_start_education"),
            educational_level=self._get_value("educational_level"),
            course_program=self._get_value("course_program"),
            year_level=self._get_value("year_level"),
            semester=self._get_value("semester"),
            enrollment_status=self._get_value("enrollment_status"),
            visa_category=self._get_value("visa_category"),
            visa_grant_date=self._get_value("visa_grant_date"),
            visa_validity_date=self._get_value("visa_validity_date"),
            visa_status=self._get_value("visa_status"),
            remarks=self._get_value("remarks"),
        )

    def _load_record(self):
        """Load existing record data into form fields."""
        record = self._record_service.get_record(self._record_id)
        if not record:
            QMessageBox.warning(self, "Error", "Record not found")
            self.cancelled.emit()
            return

        field_map = record.to_dict()
        for key, value in field_map.items():
            if key in self._fields:
                self._set_value(key, str(value) if value else "")

    # ── Save / Cancel ──

    def _on_save(self) -> bool:
        """Validate and save the record. Returns True if save succeeded."""
        if not self._validate():
            return False

        record = self._build_record()

        try:
            if self._record_id:
                self._record_service.update_record(self._record_id, record)
                record_id = self._record_id
            else:
                record_id = self._record_service.create_record(record)

            # Delete draft on successful save
            self._delete_draft()
            self._autosave_timer.stop()
            self.saved.emit(record_id)
            return True
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
            return False
        except Exception as e:
            logger.error("Failed to save record: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to save record:\n{e}")
            return False

    def _on_cancel(self):
        """Handle cancel with unsaved changes check."""
        if self.confirm_discard():
            self._autosave_timer.stop()
            self.cancelled.emit()
