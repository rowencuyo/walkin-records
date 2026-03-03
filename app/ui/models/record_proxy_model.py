"""
QSortFilterProxyModel for client-side sorting and instant search filtering.

Design note: The primary search/filter is handled server-side in
RecordService.search_records() for pagination. This proxy model provides
an additional client-side instant filter for the current page of data,
giving immediate feedback without re-querying the database.
"""
from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex


class RecordProxyModel(QSortFilterProxyModel):
    """Proxy model with client-side sorting and instant search filter."""

    SEARCH_ROLE = Qt.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_terms: list[str] = []
        self.setDynamicSortFilter(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)

    def set_search_text(self, text: str):
        """Set the search text for client-side filtering (multi-word AND)."""
        new_terms = text.lower().split() if text.strip() else []
        if new_terms != self._search_terms:
            self._search_terms = new_terms
            self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._search_terms:
            return True

        model = self.sourceModel()
        if model is None:
            return True

        # Get the composite search string from the source model
        index = model.index(source_row, 0, source_parent)
        search_text = model.data(index, self.SEARCH_ROLE)
        if not search_text:
            return False

        search_lower = search_text.lower()
        # AND logic: every search term must appear somewhere
        return all(term in search_lower for term in self._search_terms)
