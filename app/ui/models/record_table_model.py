"""
QAbstractTableModel for walk-in records.
Uses server-side pagination — data is loaded in pages from the database.
"""
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex

from app.models import WalkInRecord


COLUMNS = [
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

    # ── Data interface ──

    def set_data(self, records: list[WalkInRecord], total_count: int):
        """Replace current data."""
        self.beginResetModel()
        self._records = records
        self._total_count = total_count
        self.endResetModel()

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

    # ── QAbstractTableModel implementation ──

    def rowCount(self, parent=QModelIndex()):
        return len(self._records)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        record = self._records[index.row()]
        col_key = COLUMNS[index.column()][0]

        if role == Qt.DisplayRole:
            if col_key == "full_name":
                return record.full_name
            return getattr(record, col_key, "")

        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.UserRole:
            return record.id

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNS[section][1]
        return None

    def sort(self, column, order=Qt.AscendingOrder):
        """Sort by column. Emits layoutChanged."""
        if 0 <= column < len(COLUMNS):
            col_key = COLUMNS[column][0]
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
