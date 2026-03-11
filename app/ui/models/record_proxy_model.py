"""
QSortFilterProxyModel for client-side sorting and instant search filtering.

Design note: The primary search/filter is handled server-side in
RecordService.search_records() for pagination. This proxy model provides
an additional client-side instant filter for the current page of data,
giving immediate feedback without re-querying the database.
"""
from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex

COMPLETENESS_ROLE = Qt.UserRole + 2
ACTIVE_STATUS_ROLE = Qt.UserRole + 3

# Priority order: Ok (1) → !! (2) → Inc (3) → None (4)
_COMPLETENESS_PRIORITY = {
    "complete": 1,
    "missing_fields": 2,
    "incomplete_documents": 3,
    "no_documents": 4,
}


class RecordProxyModel(QSortFilterProxyModel):
    """Proxy model with client-side sorting and instant search filter."""

    SEARCH_ROLE = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_terms: list[str] = []
        self._active_status: str = "active"
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)

    def set_search_text(self, text: str):
        """Set the search text for client-side filtering (multi-word AND)."""
        new_terms = text.lower().split() if text.strip() else []
        if new_terms != self._search_terms:
            self._search_terms = new_terms
            self.invalidateFilter()

    def set_active_status(self, status: str):
        """Set the active status filter for client-side filtering."""
        if self._active_status != status:
            self._active_status = status
            self.invalidateFilter()

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """Custom sort: Document column sorts by priority, not alphabetically."""
        if left.column() == 0:
            left_status = self.sourceModel().data(left, COMPLETENESS_ROLE) or ""
            right_status = self.sourceModel().data(right, COMPLETENESS_ROLE) or ""
            left_priority = _COMPLETENESS_PRIORITY.get(left_status, 99)
            right_priority = _COMPLETENESS_PRIORITY.get(right_status, 99)
            return left_priority < right_priority
        return super().lessThan(left, right)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if model is None:
            return True

        # 1. Filter by active status
        index = model.index(source_row, 0, source_parent)
        is_active = model.data(index, ACTIVE_STATUS_ROLE)
        
        if self._active_status == "active" and not is_active:
            return False
        if self._active_status == "archived" and is_active:
            return False

        # 2. Filter by search terms
        if not self._search_terms:
            return True

        search_text = model.data(index, self.SEARCH_ROLE)
        if not search_text:
            return False

        search_lower = search_text.lower()
        # AND logic: every search term must appear somewhere
        return all(term in search_lower for term in self._search_terms)

