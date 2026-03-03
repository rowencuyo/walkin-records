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

        back_btn = QPushButton("Back")
        back_btn.setFixedHeight(38)
        back_btn.clicked.connect(self.back_requested.emit)
        header.addWidget(back_btn)

        self._title_label = QLabel("Profile")
        self._title_label.setObjectName("pageTitle")
        header.addWidget(self._title_label)
        header.addStretch()

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setObjectName("primaryButton")
        self._edit_btn.setFixedHeight(38)
        self._edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._record_id))
        self._edit_btn.setVisible(not self._read_only)
        header.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setObjectName("dangerButton")
        self._delete_btn.setFixedHeight(38)
        self._delete_btn.clicked.connect(self._on_delete)
        self._delete_btn.setVisible(not self._read_only)
        header.addWidget(self._delete_btn)

        self._restore_btn = QPushButton("Restore")
        self._restore_btn.setObjectName("primaryButton")
        self._restore_btn.setFixedHeight(38)
        self._restore_btn.clicked.connect(self._on_restore)
        self._restore_btn.setVisible(False)
        header.addWidget(self._restore_btn)

        outer.addLayout(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self._content = QWidget()
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

        # Completeness banner
        documents = self._document_service.get_documents(self._record_id)
        doc_types = [d.document_type for d in documents]
        status, missing_items = check_completeness(self._record, len(documents), doc_types)
        if status != "complete":
            banner = QLabel("Incomplete: " + ", ".join(missing_items))
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
        self._pic_widget = ProfilePictureWidget(size=140, editable=not self._read_only)
        pic_path = self._image_service.get_profile_picture_path(self._record_id)
        self._pic_widget.set_image(pic_path)
        if not self._read_only:
            self._pic_widget.upload_requested.connect(self._on_upload_picture)
            self._pic_widget.remove_requested.connect(self._on_remove_picture)

        pic_container = QWidget()
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

        top_widget = QWidget()
        top_widget.setLayout(top)
        self._content_layout.addWidget(top_widget)

        # Inactive banner
        if not is_active:
            banner = QLabel("This record is inactive (soft-deleted)")
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
        ]))

        # Visa
        self._content_layout.addWidget(self._create_info_section("Visa Information", [
            ("Visa Category", self._record.visa_category),
            ("Visa Grant Date", self._record.visa_grant_date),
            ("Visa Validity Date", self._record.visa_validity_date),
            ("Status", self._record.visa_status),
            ("Remarks", self._record.remarks),
        ]))

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

    def _create_info_section(self, title: str, fields: list[tuple[str, str]]) -> QGroupBox:
        """Create a read-only info section."""
        group = QGroupBox(title)
        layout = QFormLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        for label, value in fields:
            lbl = QLabel(label)
            lbl.setObjectName("fieldLabel")
            val = QLabel(value if value else "---")
            val.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val.setWordWrap(True)
            layout.addRow(lbl, val)

        group.setLayout(layout)
        return group

    def _create_documents_section(self, documents: list[Document]) -> QGroupBox:
        """Create the documents section with upload, integrity checks, and file list."""
        group = QGroupBox("Documents")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 16, 12, 12)

        # Upload button (hidden in read-only mode)
        if not self._read_only:
            upload_btn = QPushButton("+ Upload Document")
            upload_btn.setFixedHeight(36)
            upload_btn.clicked.connect(self._on_upload_document)
            layout.addWidget(upload_btn, alignment=Qt.AlignLeft)

        if not documents:
            no_docs = QLabel("No documents uploaded")
            no_docs.setObjectName("subtitleLabel")
            layout.addWidget(no_docs)
        else:
            for doc in documents:
                row = QHBoxLayout()
                row.setSpacing(8)

                # Check file integrity
                file_exists = Path(doc.file_path).exists() if doc.file_path else False

                if file_exists:
                    icon = QLabel("[OK]")
                    icon.setStyleSheet("color: #34C759; font-weight: 600;")
                else:
                    icon = QLabel("[!!]")
                    icon.setStyleSheet("color: #FF3B30; font-weight: 600;")
                icon.setFixedWidth(40)
                row.addWidget(icon)

                info = QVBoxLayout()
                info.setSpacing(2)
                name_lbl = QLabel(f"{doc.document_type}")
                name_lbl.setStyleSheet("font-weight: 500;")
                info.addWidget(name_lbl)

                if file_exists:
                    meta = QLabel(f"{doc.file_name} | {doc.file_size / 1024:.1f} KB | {doc.upload_date}")
                else:
                    meta = QLabel(f"{doc.file_name} | MISSING FILE")
                    meta.setStyleSheet("color: #FF3B30;")
                meta.setObjectName("subtitleLabel")
                info.addWidget(meta)
                row.addLayout(info, stretch=1)

                if file_exists:
                    open_btn = QPushButton("Open")
                    open_btn.setFixedHeight(34)
                    open_btn.clicked.connect(lambda checked, d=doc: self._open_document(d))
                    row.addWidget(open_btn)
                else:
                    # Locate button for missing files
                    locate_btn = QPushButton("Locate")
                    locate_btn.setFixedHeight(34)
                    locate_btn.clicked.connect(lambda checked, d=doc: self._locate_document(d))
                    row.addWidget(locate_btn)

                if not self._read_only:
                    del_btn = QPushButton("Remove")
                    del_btn.setObjectName("dangerButton")
                    del_btn.setFixedHeight(34)
                    del_btn.setMinimumWidth(80)
                    del_btn.clicked.connect(lambda checked, d=doc: self._delete_document(d))
                    row.addWidget(del_btn)

                row_widget = QWidget()
                row_widget.setLayout(row)
                row_widget.setStyleSheet(
                    f"background-color: {Colors.BG_SECONDARY}; border-radius: 6px; padding: 8px 12px;"
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

        ext_filter = " ".join(f"*{e}" for e in ALLOWED_DOCUMENT_EXTENSIONS)
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Document", "", f"Documents ({ext_filter})"
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
        path, _ = QFileDialog.getOpenFileName(
            self, f"Locate: {doc.file_name}", "", "All Files (*.*)"
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
                # Push undo action
                self.undo_requested.emit(
                    "document_delete",
                    f"Delete {doc.document_type}",
                    lambda: None,  # Document file already deleted, no undo for file
                )
                self._load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete document:\n{e}")

    # -- Profile Picture Actions --

    def _on_upload_picture(self):
        ext_filter = " ".join(f"*{e}" for e in sorted(ALLOWED_IMAGE_EXTENSIONS))
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Profile Picture", "",
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
