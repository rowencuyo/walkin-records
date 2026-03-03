"""
Add / Edit record form with full validation.
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QTextEdit, QLabel, QPushButton, QScrollArea,
    QFrame, QGroupBox, QMessageBox, QCompleter,
)

from app.constants import (
    Sex, VisaStatus, EducationalLevel, Semester,
    VISA_CATEGORIES, YEAR_LEVELS, COUNTRIES,
)
from app.models import WalkInRecord
from app.services.record_service import RecordService
from app.utils.validators import (
    validate_required, validate_date_required, validate_date, validate_passport,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RecordForm(QWidget):
    """Form for creating or editing a walk-in record."""

    saved = Signal(int)      # Emits record ID on save
    cancelled = Signal()

    def __init__(self, record_id: int | None = None, parent=None):
        super().__init__(parent)
        self._record_id = record_id
        self._record_service = RecordService()
        self._fields: dict[str, QWidget] = {}
        self._error_labels: dict[str, QLabel] = {}
        self._setup_ui()

        if record_id:
            self._load_record()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title_text = "Edit Record" if self._record_id else "Add New Record"
        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(38)
        cancel_btn.clicked.connect(self.cancelled.emit)
        header.addWidget(cancel_btn)

        save_btn = QPushButton("Save Record")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(38)
        save_btn.clicked.connect(self._on_save)
        header.addWidget(save_btn)

        outer.addLayout(header)

        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(16)
        form_layout.setContentsMargins(0, 0, 12, 0)

        # Section: Identity
        form_layout.addWidget(self._create_section("Identity", [
            ("last_name", "Last Name *", "line"),
            ("first_name", "First Name *", "line"),
            ("middle_name", "Middle Name", "line"),
            ("sex", "Sex *", "combo", [s.value for s in Sex]),
            ("date_of_birth", "Date of Birth * (YYYY-MM-DD)", "line"),
            ("passport_number", "Passport Number *", "line"),
            ("country_of_citizenship", "Country of Citizenship *", "combo", COUNTRIES),
        ]))

        # Section: Philippine Residential Address
        form_layout.addWidget(self._create_section("Philippine Residential Address", [
            ("street", "Street", "line"),
            ("barangay", "Barangay", "line"),
            ("city_municipality", "City / Municipality", "line"),
            ("province", "Province", "line"),
        ]))

        # Section: Academic & Residency
        form_layout.addWidget(self._create_section("Academic & Residency Information", [
            ("date_of_arrival", "Date of Arrival (YYYY-MM-DD)", "line"),
            ("date_start_education", "Date of Start of Education (YYYY-MM-DD)", "line"),
            ("educational_level", "Educational Level", "combo", [el.value for el in EducationalLevel]),
            ("course_program", "Course / Program", "line"),
            ("year_level", "Year Level", "combo", YEAR_LEVELS),
            ("semester", "Semester", "combo", [s.value for s in Semester]),
        ]))

        # Section: Visa Information
        form_layout.addWidget(self._create_section("Visa Information", [
            ("visa_category", "Visa Category", "combo", VISA_CATEGORIES),
            ("visa_grant_date", "Visa Grant Date (YYYY-MM-DD)", "line"),
            ("visa_validity_date", "Visa Validity Date (YYYY-MM-DD)", "line"),
            ("visa_status", "Status", "combo", [vs.value for vs in VisaStatus]),
            ("remarks", "Remarks", "text"),
        ]))

        form_layout.addStretch()
        scroll.setWidget(form_widget)
        outer.addWidget(scroll, stretch=1)

    def _create_section(self, title: str, fields: list) -> QGroupBox:
        """Create a form section group box."""
        group = QGroupBox(title)
        layout = QFormLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        for field_def in fields:
            key = field_def[0]
            label = field_def[1]
            field_type = field_def[2]

            # Create the input widget
            if field_type == "line":
                widget = QLineEdit()
                widget.setMaximumWidth(400)
            elif field_type == "combo":
                options = field_def[3] if len(field_def) > 3 else []
                widget = QComboBox()
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
                widget.setMaximumWidth(400)
            elif field_type == "text":
                widget = QTextEdit()
                widget.setMaximumWidth(400)
                widget.setFixedHeight(100)
            else:
                widget = QLineEdit()

            self._fields[key] = widget

            # Error label
            err = QLabel()
            err.setObjectName("errorLabel")
            err.setVisible(False)
            self._error_labels[key] = err

            # Wrap widget + error in a vertical layout
            wrapper = QVBoxLayout()
            wrapper.setSpacing(2)
            wrapper.addWidget(widget)
            wrapper.addWidget(err)

            lbl = QLabel(label)
            lbl.setObjectName("fieldLabel")
            layout.addRow(lbl, wrapper)

        group.setLayout(layout)
        return group

    def _get_value(self, key: str) -> str:
        """Get value from a field widget."""
        widget = self._fields.get(key)
        if isinstance(widget, QLineEdit):
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
        if isinstance(widget, QLineEdit):
            widget.setText(value)
        elif isinstance(widget, QComboBox):
            idx = widget.findData(value)
            if idx >= 0:
                widget.setCurrentIndex(idx)
            elif widget.isEditable():
                widget.setCurrentText(value)
        elif isinstance(widget, QTextEdit):
            widget.setPlainText(value)

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

    def _build_record(self) -> WalkInRecord:
        """Build a WalkInRecord from form values."""
        return WalkInRecord(
            last_name=self._get_value("last_name"),
            first_name=self._get_value("first_name"),
            middle_name=self._get_value("middle_name"),
            sex=self._get_value("sex"),
            date_of_birth=self._get_value("date_of_birth"),
            passport_number=self._get_value("passport_number"),
            country_of_citizenship=self._get_value("country_of_citizenship"),
            street=self._get_value("street"),
            barangay=self._get_value("barangay"),
            city_municipality=self._get_value("city_municipality"),
            province=self._get_value("province"),
            date_of_arrival=self._get_value("date_of_arrival"),
            date_start_education=self._get_value("date_start_education"),
            educational_level=self._get_value("educational_level"),
            course_program=self._get_value("course_program"),
            year_level=self._get_value("year_level"),
            semester=self._get_value("semester"),
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

    def _on_save(self):
        """Validate and save the record."""
        if not self._validate():
            return

        record = self._build_record()

        try:
            if self._record_id:
                self._record_service.update_record(self._record_id, record)
                record_id = self._record_id
            else:
                record_id = self._record_service.create_record(record)

            self.saved.emit(record_id)
        except ValueError as e:
            QMessageBox.warning(self, "Validation Error", str(e))
        except Exception as e:
            logger.error("Failed to save record: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to save record:\n{e}")
