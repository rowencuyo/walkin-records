"""
QSortFilterProxyModel for client-side filtering (secondary to server-side).
"""
from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex


class RecordProxyModel(QSortFilterProxyModel):
    """Proxy model for additional client-side filtering and sorting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
