"""
Batch Operations Toolbar - Multi-select records with bulk actions.
Provides checkboxes, select-all, and bulk action buttons.
"""
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QCheckBox,
    QFrame, QSpacerItem,
)

from app.ui.theme import Colors, Typography
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BatchOperationsToolbar(QFrame):
    """Toolbar for multi-select batch operations."""
    
    # Signals
    select_all_toggled = Signal(bool)  # Emits True/False when Select All toggled
    export_selected = Signal(list)     # Emits list of selected record IDs
    archive_selected = Signal(list)    # Emits list of record IDs to archive
    tag_selected = Signal(list, str)   # Emits (record_ids, tag_name)
    delete_selected = Signal(list)     # Emits list of record IDs to delete
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("batchToolbar")
        self.setStyleSheet(f"""
            #batchToolbar {{
                background-color: {Colors.ACCENT_LIGHT};
                border: 1px solid {Colors.ACCENT};
                border-radius: 8px;
                padding: 12px 16px;
            }}
        """)
        
        self._selected_records = set()
        self._setup_ui()
        self.hide()  # Hidden by default, shown when records selected
    
    def _setup_ui(self):
        """Setup the toolbar layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Select All checkbox
        self.select_all_cb = QCheckBox("Select All", self)
        self.select_all_cb.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT_PRIMARY};
                spacing: 6px;
                font-weight: 500;
            }}
        """)
        self.select_all_cb.toggled.connect(self._on_select_all_toggled)
        layout.addWidget(self.select_all_cb)
        
        # Selection count
        self.count_label = QLabel("0 selected", self)
        self.count_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: {Typography.SIZE_SM}px;
            font-weight: 500;
        """)
        layout.addWidget(self.count_label)
        
        # Separator
        separator = QFrame(self)
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet(f"background-color: {Colors.BORDER_LIGHT};")
        separator.setFixedWidth(1)
        layout.addWidget(separator)
        
        # Action buttons
        self.export_btn = QPushButton("📥 Export", self)
        self.export_btn.setFixedHeight(32)
        self.export_btn.clicked.connect(self._on_export)
        layout.addWidget(self.export_btn)
        
        self.archive_btn = QPushButton("📦 Archive", self)
        self.archive_btn.setFixedHeight(32)
        self.archive_btn.clicked.connect(self._on_archive)
        layout.addWidget(self.archive_btn)
        
        self.tag_btn = QPushButton("🏷️ Tag", self)
        self.tag_btn.setFixedHeight(32)
        self.tag_btn.clicked.connect(self._on_tag)
        layout.addWidget(self.tag_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete", self)
        self.delete_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.DANGER_LIGHT};
                color: {Colors.DANGER};
                border: 1px solid {Colors.DANGER};
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {Colors.DANGER};
                color: white;
            }}
        """)
        self.delete_btn.setFixedHeight(32)
        self.delete_btn.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_btn)
        
        # Stretch
        layout.addStretch()
        
        # Close button
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(32, 32)
        self.close_btn.clicked.connect(self.deselect_all)
        layout.addWidget(self.close_btn)
    
    def select_record(self, record_id: int):
        """Add record to selection."""
        self._selected_records.add(record_id)
        self._update_ui()
    
    def deselect_record(self, record_id: int):
        """Remove record from selection."""
        self._selected_records.discard(record_id)
        self._update_ui()
    
    def toggle_record(self, record_id: int):
        """Toggle record selection."""
        if record_id in self._selected_records:
            self.deselect_record(record_id)
        else:
            self.select_record(record_id)
    
    def select_all(self, total_count: int):
        """Select all records."""
        # This is called by parent when Select All is toggled
        self.show()
        self.select_all_cb.setChecked(True, block=True) if hasattr(self.select_all_cb, 'setChecked') else None
    
    def deselect_all(self):
        """Clear all selections."""
        self._selected_records.clear()
        self.select_all_cb.setChecked(False)
        self._update_ui()
    
    def _on_select_all_toggled(self, checked: bool):
        """Handle Select All checkbox toggle."""
        self.select_all_toggled.emit(checked)
    
    def _update_ui(self):
        """Update toolbar UI based on selection."""
        count = len(self._selected_records)
        self.count_label.setText(f"{count} selected")
        
        if count > 0:
            self.show()
        else:
            self.hide()
            self.select_all_cb.setChecked(False)
    
    def _on_export(self):
        """Emit export signal with selected records."""
        self.export_selected.emit(list(self._selected_records))
        logger.info(f"Exporting {len(self._selected_records)} records")
    
    def _on_archive(self):
        """Emit archive signal."""
        self.archive_selected.emit(list(self._selected_records))
        logger.info(f"Archiving {len(self._selected_records)} records")
    
    def _on_tag(self):
        """Emit tag signal (placeholder for tag dialog)."""
        tag_name = "Important"  # Would be from a dialog
        self.tag_selected.emit(list(self._selected_records), tag_name)
        logger.info(f"Tagging {len(self._selected_records)} records with '{tag_name}'")
    
    def _on_delete(self):
        """Emit delete signal (with confirmation needed)."""
        self.delete_selected.emit(list(self._selected_records))
        logger.info(f"Deleting {len(self._selected_records)} records")
    
    def get_selected_records(self) -> list[int]:
        """Get list of selected record IDs."""
        return list(self._selected_records)
    
    def set_total_count(self, total: int):
        """Set total record count for Select All context."""
        self._total_count = total


class SelectableRecordCheckBox(QCheckBox):
    """Checkbox for record selection in list/table views."""
    
    toggled_safe = Signal(int, bool)  # Emits (record_id, is_checked)
    
    def __init__(self, record_id: int, parent=None):
        super().__init__(parent)
        self._record_id = record_id
        self.setStyleSheet(f"""
            QCheckBox {{
                spacing: 8px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
            QCheckBox::indicator:checked {{
                background-color: {Colors.ACCENT};
                border: 1px solid {Colors.ACCENT};
                border-radius: 3px;
            }}
        """)
        self.toggled.connect(self._on_toggled)
    
    def _on_toggled(self, checked: bool):
        """Emit record_id along with toggled state."""
        self.toggled_safe.emit(self._record_id, checked)
    
    def get_record_id(self) -> int:
        """Get the record ID this checkbox represents."""
        return self._record_id
