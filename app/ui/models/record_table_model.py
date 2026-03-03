"""
QAbstractTableModel for walk-in records.
Uses server-side pagination -- data is loaded in pages from the database.
Provides custom roles for search and completeness.
"""
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

from app.models import WalkInRecord

SEARCH_ROLE = Qt.UserRole + 1
COMPLETENESS_ROLE = Qt.UserRole + 2

COLUMNS = [
    ("completeness", ""),
    ("full_name", "Name"),
    ("passport_number", "Passport"),
    ("visa_category", "Visa Category"),
    ("visa_status", "Status"),
    ("course_program", "Course / Program"),
    ("year_level", "Year"),
    ("educational_level", "Level"),
    ("country_of_citizenship", "Country"),
]


class RecordTableModel(QAbstractTableModel):
    """Table model backed by a list of WalkInRecord objects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: list[WalkInRecord] = []
        self._total_count: int = 0
        self._doc_types: dict[int, list[str]] = {}  # record_id -> document types
        self._completeness: dict[int, str] = {}  # record_id -> status

    # -- Data interface --

    def set_data(
        self,
        records: list[WalkInRecord],
        total_count: int,
        doc_types: dict[int, list[str]] | None = None,
    ):
        """Replace current data."""
        self.beginResetModel()
        self._records = records
        self._total_count = total_count
        self._doc_types = doc_types or {}
        self._compute_completeness()
        self.endResetModel()

    def _compute_completeness(self):
        """Pre-compute completeness status for all records."""
        from app.services.completeness import check_completeness
        self._completeness = {}
        for r in self._records:
            types = self._doc_types.get(r.id, [])
            status, _ = check_completeness(r, len(types), types)
            self._completeness[r.id] = status

    def get_record(self, row: int) -> WalkInRecord | None:
        if 0 <= row < len(self._records):
            return self._records[row]
        return None

    def get_record_by_index(self, index: QModelIndex) -> WalkInRecord | None:
        if index.isValid():
            return self.get_record(index.row())
        return None

    @property
    def total_count(self) -> int:
        return self._total_count

    # -- QAbstractTableModel implementation --

    def rowCount(self, parent=QModelIndex()):
        return len(self._records)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        if row < 0 or row >= len(self._records):
            return None

        record = self._records[row]
        col_key = COLUMNS[index.column()][0]

        if role == Qt.DisplayRole:
            if col_key == "completeness":
                status = self._completeness.get(record.id, "")
                if status == "complete":
                    return "OK"
                elif status == "missing_fields":
                    return "!!"
                elif status == "incomplete_documents":
                    return "DOC"
                elif status == "no_documents":
                    return "---"
                return ""
            if col_key == "full_name":
                return record.full_name or ""
            return getattr(record, col_key, "") or ""

        if role == Qt.ForegroundRole:
            if col_key == "completeness":
                status = self._completeness.get(record.id, "")
                from PySide6.QtGui import QColor
                if status == "complete":
                    return QColor("#34C759")
                elif status in ("missing_fields", "incomplete_documents", "no_documents"):
                    return QColor("#FF9500")
            return None

        if role == Qt.TextAlignmentRole:
            if col_key == "completeness":
                return Qt.AlignCenter | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.UserRole:
            return record.id

        if role == SEARCH_ROLE:
            # Composite search string for proxy model filtering
            parts = [
                record.first_name, record.middle_name, record.last_name,
                record.passport_number, record.country_of_citizenship,
                record.course_program, record.visa_category, record.visa_status,
                record.educational_level, record.year_level,
                record.city_municipality, record.province, record.remarks,
                record.full_name,
            ]
            return " ".join(p for p in parts if p)

        if role == COMPLETENESS_ROLE:
            return self._completeness.get(record.id, "")

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNS[section][1]
        return None

    def sort(self, column, order=Qt.AscendingOrder):
        """Sort by column. Emits layoutChanged."""
        if 0 <= column < len(COLUMNS):
            col_key = COLUMNS[column][0]
            if col_key == "completeness":
                return  # Don't sort by indicator
            reverse = order == Qt.DescendingOrder
            self.layoutAboutToBeChanged.emit()
            if col_key == "full_name":
                self._records.sort(
                    key=lambda r: r.full_name.lower(), reverse=reverse
                )
            else:
                self._records.sort(
                    key=lambda r: (getattr(r, col_key, "") or "").lower(),
                    reverse=reverse,
                )
            self.layoutChanged.emit()
