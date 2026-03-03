"""
QSortFilterProxyModel for client-side sorting.

Design note: All search and filter logic is handled server-side in
RecordService.search_records() because the app uses server-side pagination.
The proxy model is intentionally kept simple - it provides client-side sorting
and case-insensitive collation but does NOT override filterAcceptsRow, since
the database already returns only the matching rows for each page.
"""
from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex


class RecordProxyModel(QSortFilterProxyModel):
    """Proxy model for client-side sorting on paginated server-side data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
