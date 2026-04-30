"""
Full profile view with document management, profile pictures,
completeness indicators, file integrity warnings, and undo support.
"""
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGroupBox, QFormLayout, QMessageBox,
    QFileDialog, QGridLayout, QSizePolicy, QSpacerItem,
)

from app.models import WalkInRecord, Document
from app.services.record_service import RecordService
from app.services.document_service import DocumentService
from app.services.image_service import ImageService
from app.services.completeness import check_completeness
from app.constants import DocumentType, ALLOWED_DOCUMENT_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS
from app.ui.components.profile_pic import ProfilePictureWidget
from app.ui.theme import Colors
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ProfileView(QWidget):
    """Read-only full profile display with document management."""

    edit_requested = Signal(int)
    back_requested = Signal()
    record_deleted = Signal()
    undo_requested = Signal(str, str, object)  # (action_type, description, callback)

    def __init__(self, record_id: int, read_only: bool = False, parent=None):
        super().__init__(parent)
        self._record_id = record_id
        self._read_only = read_only
        self._record_service = RecordService()
        self._document_service = DocumentService()
        self._image_service = ImageService()
        self._record: WalkInRecord | None = None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 16)
        outer.setSpacing(12)

        # Header
        header = QHBoxLayout()

        back_btn = QPushButton("Back", self)
        back_btn.setFixedHeight(38)
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)

        self._title_label = QLabel("Profile", self)
        self._title_label.setObjectName("pageTitle")
        # A4 — let title absorb available space so it dominates the header
        self._title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        header.addWidget(self._title_label)
        header.addStretch()
        header.setSpacing(12)

        self._edit_btn = QPushButton("Edit", self)
        self._edit_btn.setObjectName("primaryButton")
        self._edit_btn.setFixedHeight(38)
        self._edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._record_id))
        self._edit_btn.setVisible(not self._read_only)
        header.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete", self)
        self._delete_btn.setObjectName("dangerButton")
        self._delete_btn.setFixedHeight(38)
        self._delete_btn.clicked.connect(self._on_delete)
        self._delete_btn.setVisible(not self._read_only)
        header.addWidget(self._delete_btn)

        self._restore_btn = QPushButton("Restore", self)
        self._restore_btn.setObjectName("primaryButton")
        self._restore_btn.setFixedHeight(38)
        self._restore_btn.clicked.connect(self._on_restore)
        self._restore_btn.setVisible(False)
        header.addWidget(self._restore_btn)

        outer.addLayout(header)

        # Scroll area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget(scroll)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(16)
        self._content_layout.setContentsMargins(0, 0, 12, 0)

        scroll.setWidget(self._content)
        outer.addWidget(scroll, stretch=1)

    def _load_data(self):
        """Load record and populate the view."""
        self._record = self._record_service.get_record(self._record_id)
        if not self._record:
            QMessageBox.warning(self, "Error", "Record not found")
            self.back_requested.emit()
            return

        self._title_label.setText(self._record.full_name)

        # Show/hide buttons based on active status and read-only mode
        is_active = self._record.is_active
        self._delete_btn.setVisible(is_active and not self._read_only)
        self._restore_btn.setVisible(not is_active and not self._read_only)
        self._edit_btn.setVisible(not self._read_only)

        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        # C3 — guard document fetch so a DB error doesn't break the whole view
        try:
            documents = self._document_service.get_documents(self._record_id)
        except Exception as e:
            logger.warning("Could not load documents for record %d: %s", self._record_id, e)
            documents = []
        doc_types = [d.document_type for d in documents]
        status, missing_items = check_completeness(self._record, len(documents), doc_types)
        if status != "complete":
            banner = QLabel("Incomplete: " + ", ".join(missing_items), self)
            banner.setStyleSheet(
                f"background-color: {Colors.WARNING}; color: white; padding: 8px 16px; "
                f"border-radius: 6px; font-weight: 600;"
            )
            banner.setAlignment(Qt.AlignCenter)
            banner.setWordWrap(True)
            self._content_layout.addWidget(banner)

        # Top section: Profile picture + Identity
        top = QHBoxLayout()

        # Profile picture
        self._pic_widget = ProfilePictureWidget(size=140, editable=not self._read_only, parent=self)
        pic_path = self._image_service.get_profile_picture_path(self._record_id)
        self._pic_widget.set_image(pic_path)
        if not self._read_only:
            self._pic_widget.upload_requested.connect(self._on_upload_picture)
            self._pic_widget.remove_requested.connect(self._on_remove_picture)

        pic_container = QWidget(self)
        pic_layout = QVBoxLayout(pic_container)
        pic_layout.setContentsMargins(0, 0, 24, 0)
        pic_layout.addWidget(self._pic_widget, alignment=Qt.AlignTop)
        top.addWidget(pic_container)

        # Identity section
        identity_group = self._create_info_section("Identity", [
            ("Full Name", self._record.full_name),
            ("Sex", self._record.sex),
            ("Date of Birth", self._record.date_of_birth),
            ("Passport Number", self._record.passport_number),
            ("Country of Citizenship", self._record.country_of_citizenship),
        ])
        top.addWidget(identity_group, stretch=1)

        top_widget = QWidget(self)
        top_widget.setLayout(top)
        self._content_layout.addWidget(top_widget)

        # Inactive banner
        if not is_active:
            banner = QLabel("This record is inactive (soft-deleted)", self)
            banner.setStyleSheet(
                f"background-color: {Colors.WARNING}; color: white; padding: 8px 16px; "
                f"border-radius: 6px; font-weight: 600;"
            )
            banner.setAlignment(Qt.AlignCenter)
            self._content_layout.addWidget(banner)

        # Address
        self._content_layout.addWidget(self._create_info_section("Philippine Residential Address", [
            ("Street", self._record.street),
            ("Barangay", self._record.barangay),
            ("City / Municipality", self._record.city_municipality),
            ("Province", self._record.province),
        ]))

        # Academic & Residency
        self._content_layout.addWidget(self._create_info_section("Academic & Residency Info", [
            ("Date of Arrival", self._record.date_of_arrival),
            ("Date of Start of Education", self._record.date_start_education),
            ("Educational Level", self._record.educational_level),
            ("Course / Program", self._record.course_program),
            ("Year Level", self._record.year_level),
            ("Semester", self._record.semester),
            ("Remarks", self._record.enrollment_status),
        ]))

        # Visa — D1: inject countdown badge next to validity date
        visa_row = QHBoxLayout()
        visa_badge = self._make_visa_badge(self._record.visa_validity_date)
        if visa_badge:
            visa_row.addWidget(visa_badge)
        visa_row_widget = QWidget(self)
        visa_row_widget.setLayout(visa_row)
        self._content_layout.addWidget(
            self._create_info_section("Visa Information", [
                ("Visa Category", self._record.visa_category),
                ("Visa Grant Date", self._record.visa_grant_date),
                ("Visa Validity Date", self._record.visa_validity_date),
                ("Status", self._record.visa_status),
                ("Comments", self._record.remarks),
            ])
        )
        if visa_badge:
            self._content_layout.addWidget(visa_row_widget)

        # Documents (with file integrity checks)
        self._content_layout.addWidget(
            self._create_documents_section(documents)
        )

        # Metadata
        self._content_layout.addWidget(self._create_info_section("Record Metadata", [
            ("Record ID", str(self._record.id)),
            ("Created At", self._record.created_at),
            ("Updated At", self._record.updated_at),
            ("Status", "Active" if self._record.is_active else "Inactive"),
        ]))

        self._content_layout.addStretch()


    # ── D1: Visa Countdown Badge ──────────────────────────────────────────────

    def _make_visa_badge(self, validity_date: str) -> "QLabel | None":
        """Return a color-coded days-remaining badge for the visa validity date.

        Returns None if the date is blank or cannot be parsed.
        Colors: green > 30 days, amber ≤ 30 days, red = already expired.
        """
        if not validity_date:
            return None
        try:
            from datetime import date as _date
            exp = _date.fromisoformat(validity_date)
            days_left = (exp - _date.today()).days
        except (ValueError, TypeError):
            return None

        if days_left < 0:
            text = f"Visa expired {abs(days_left)} day{'s' if abs(days_left) != 1 else ''} ago"
            bg = "#FF3B30"
        elif days_left <= 30:
            text = f"Visa expires in {days_left} day{'s' if days_left != 1 else ''}"
            bg = "#FF9500"
        else:
            text = f"Visa valid — {days_left} days remaining"
            bg = "#34C759"

        badge = QLabel(text, self)
        badge.setStyleSheet(
            f"background-color: {bg}; color: white; font-weight: 600; font-size: 13px; "
            f"padding: 6px 14px; border-radius: 6px;"
        )
        badge.setAlignment(Qt.AlignCenter)
        return badge

    def _create_info_section(self, title: str, fields: list[tuple[str, str]]) -> QGroupBox:

        """Create a read-only info section."""
        group = QGroupBox(title, self)
        layout = QFormLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        for label, value in fields:
            lbl = QLabel(label, self)
            lbl.setObjectName("fieldLabel")
            val = QLabel(value if value else "---", self)
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val.setWordWrap(True)
            layout.addRow(lbl, val)

        group.setLayout(layout)
        return group

    def _create_documents_section(self, documents: list[Document]) -> QGroupBox:
        """Create the documents section with upload, integrity checks, and file list."""
        group = QGroupBox("Documents", self)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 16, 12, 12)

        # Upload button (hidden in read-only mode)
        if not self._read_only:
            upload_btn = QPushButton("+ Upload Document", self)
            upload_btn.setFixedHeight(36)
            upload_btn.clicked.connect(self._on_upload_document)
            layout.addWidget(upload_btn, alignment=Qt.AlignLeft)

        if not documents:
            no_docs = QLabel("No documents uploaded", self)
            no_docs.setObjectName("subtitleLabel")
            layout.addWidget(no_docs)
        else:
            for doc in documents:
                row = QHBoxLayout()
                row.setSpacing(10)
                row.setContentsMargins(14, 10, 20, 10)

                # Check file integrity
                file_exists = Path(doc.file_path).exists() if doc.file_path else False

                if file_exists:
                    icon = QLabel("OK", self)
                    icon.setStyleSheet(
                        "color: #34C759; font-weight: 700; font-size: 13px;"
                    )
                else:
                    icon = QLabel("!!", self)
                    icon.setStyleSheet(
                        "color: #FF3B30; font-weight: 700; font-size: 13px;"
                    )
                icon.setFixedWidth(24)
                icon.setAlignment(Qt.AlignCenter)
                row.addWidget(icon)

                info = QVBoxLayout()
                info.setSpacing(2)
                name_lbl = QLabel(f"{doc.document_type}", self)
                name_lbl.setStyleSheet("font-weight: 500;")
                info.addWidget(name_lbl)

                if file_exists:
                    size_kb = (doc.file_size or 0) / 1024
                    meta = QLabel(f"{doc.file_name} | {size_kb:.1f} KB | {doc.upload_date or ''}", self)
                else:
                    meta = QLabel(f"{doc.file_name} | MISSING FILE", self)
                    meta.setStyleSheet("color: #FF3B30;")
                meta.setObjectName("subtitleLabel")
                info.addWidget(meta)
                row.addLayout(info, stretch=1)

                if file_exists:
                    open_btn = QPushButton("Open", self)
                    open_btn.setFixedHeight(41)
                    open_btn.setMinimumWidth(70)
                    open_btn.clicked.connect(lambda checked, d=doc: self._open_document(d))
                    row.addWidget(open_btn)
                else:
                    locate_btn = QPushButton("Locate", self)
                    locate_btn.setFixedHeight(41)
                    locate_btn.setMinimumWidth(70)
                    locate_btn.clicked.connect(lambda checked, d=doc: self._locate_document(d))
                    row.addWidget(locate_btn)

                if not self._read_only:
                    del_btn = QPushButton("Remove", self)
                    del_btn.setFixedHeight(41)
                    del_btn.setMinimumWidth(90)
                    del_btn.clicked.connect(lambda checked, d=doc: self._delete_document(d))
                    row.addWidget(del_btn)

                row_widget = QWidget(self)
                row_widget.setLayout(row)
                row_widget.setStyleSheet(
                    f"background-color: {Colors.BG_SECONDARY}; border-radius: 6px;"
                )
                layout.addWidget(row_widget)

        group.setLayout(layout)
        return group

    # -- Document Actions --

    def _on_upload_document(self):
        """Open file dialog and upload a document."""
        doc_types = [dt.value for dt in DocumentType]
        from PySide6.QtWidgets import QInputDialog
        doc_type, ok = QInputDialog.getItem(
            self, "Document Type", "Select document type:", doc_types, 0, False
        )
        if not ok:
            return

        # Check if this document type already exists
        existing_docs = self._document_service.get_documents(self._record_id)
        existing = [d for d in existing_docs if d.document_type == doc_type]
        if existing:
            reply = QMessageBox.question(
                self, "Replace Document",
                f"A '{doc_type}' document already exists.\n"
                f"Do you want to replace it?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
            # Delete the existing one
            for d in existing:
                self._document_service.delete_document(d.id)

        from PySide6.QtCore import QStandardPaths
        home = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        ext_filter = " ".join(f"*{e}" for e in ALLOWED_DOCUMENT_EXTENSIONS)
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", home, f"Documents ({ext_filter})"
        )
        if not path:
            return

        try:
            self._document_service.save_document(self._record_id, doc_type, path)
            self._load_data()  # Refresh
        except ValueError as e:
            QMessageBox.warning(self, "Upload Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload document:\n{e}")

    def _open_document(self, doc: Document):
        """Open document with OS default application."""
        p = Path(doc.file_path)
        if p.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
        else:
            QMessageBox.warning(self, "File Not Found", f"The file no longer exists:\n{doc.file_path}")

    def _locate_document(self, doc: Document):
        """Let user locate a missing document file."""
        from PySide6.QtCore import QStandardPaths
        home = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        path, _ = QFileDialog.getOpenFileName(
            self, f"Locate: {doc.file_name}", home, "All Files (*.*)"
        )
        if path:
            if self._document_service.relocate_document(doc.id, path):
                self._load_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to update document location.")

    def _delete_document(self, doc: Document):
        """Delete a document with confirmation."""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Remove document '{doc.document_type}' ({doc.file_name})?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                self._document_service.delete_document(doc.id)
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete document:\n{e}")

    # -- Profile Picture Actions --

    def _on_upload_picture(self):
        ext_filter = " ".join(f"*{e}" for e in sorted(ALLOWED_IMAGE_EXTENSIONS))
        from PySide6.QtCore import QStandardPaths
        home = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", home,
            f"Images ({ext_filter});;All Files (*.*)"
        )
        if not path:
            return

        # Validate file type upfront before passing to background thread
        from app.utils.validators import validate_image_file
        err = validate_image_file(path)
        if err:
            allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
            QMessageBox.warning(
                self, "Invalid File Type",
                f"The selected file is not a supported image format.\n\n"
                f"Supported formats: {allowed}\n\n"
                f"Please select a valid image file."
            )
            return

        def on_success(final_path):
            self._pic_widget.set_image(final_path)

        def on_error(msg):
            QMessageBox.warning(self, "Upload Error", msg)

        self._image_service.save_profile_picture(
            self._record_id, path, on_success=on_success, on_error=on_error
        )

    def _on_remove_picture(self):
        reply = QMessageBox.question(
            self, "Confirm Remove", "Remove the profile picture?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._image_service.delete_profile_picture(self._record_id)
            self._pic_widget.set_placeholder()

    # -- Soft Delete / Restore --

    def _on_delete(self):
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Soft-delete this record ({self._record.full_name})?\n"
            f"The record will be hidden but can be restored later.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                self._record_service.soft_delete(self._record_id)
                # Push undo action
                record_id = self._record_id
                self.undo_requested.emit(
                    "soft_delete",
                    f"Delete {self._record.full_name}",
                    lambda: self._record_service.restore(record_id),
                )
                self.record_deleted.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete:\n{e}")

    def _on_restore(self):
        try:
            self._record_service.restore(self._record_id)
            # Push undo action
            record_id = self._record_id
            self.undo_requested.emit(
                "restore",
                f"Restore {self._record.full_name}",
                lambda: self._record_service.soft_delete(record_id),
            )
            self._load_data()
        except ValueError as e:
            QMessageBox.warning(self, "Restore Error", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to restore:\n{e}")

    # -- Helpers --

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
