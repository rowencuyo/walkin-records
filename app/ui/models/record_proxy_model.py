"""
QSortFilterProxyModel for client-side sorting and instant search filtering.

Design note: The primary search/filter is handled server-side in
RecordService.search_records() for pagination. This proxy model provides
an additional client-side instant filter for the current page of data,
giving immediate feedback without re-querying the database.
"""
from PySide6.QtCore import Qt, QSortFilterProxyModel, QModelIndex, QDate

COMPLETENESS_ROLE = Qt.UserRole + 2
ACTIVE_STATUS_ROLE = Qt.UserRole + 3
COUNTRY_ROLE = Qt.UserRole + 4
ARRIVAL_DATE_ROLE = Qt.UserRole + 5
CREATED_DATE_ROLE = Qt.UserRole + 6

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
        
        # Advanced filters
        self._country_filter: str = ""
        self._completeness_filter: str = "all"
        self._arrival_date_from: QDate | None = None
        self._arrival_date_to: QDate | None = None
        self._created_date_from: QDate | None = None
        self._created_date_to: QDate | None = None
        
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

    def set_advanced_filters(self, filters: dict):
        """Set multiple advanced filters at once."""
        self._country_filter = filters.get("country", "")
        self._completeness_filter = filters.get("completeness", "all")
        
        # Parse date strings (ISO format)
        arrival_from = filters.get("arrival_date_from", "")
        arrival_to = filters.get("arrival_date_to", "")
        created_from = filters.get("created_date_from", "")
        created_to = filters.get("created_date_to", "")
        
        self._arrival_date_from = QDate.fromString(arrival_from, Qt.ISODate) if arrival_from else None
        self._arrival_date_to = QDate.fromString(arrival_to, Qt.ISODate) if arrival_to else None
        self._created_date_from = QDate.fromString(created_from, Qt.ISODate) if created_from else None
        self._created_date_to = QDate.fromString(created_to, Qt.ISODate) if created_to else None
        
        self.invalidateFilter()
    
    def set_country_filter(self, country: str):
        """Set country of citizenship filter."""
        if self._country_filter != country:
            self._country_filter = country
            self.invalidateFilter()
    
    def set_completeness_filter(self, completeness: str):
        """Set document completeness filter."""
        if self._completeness_filter != completeness:
            self._completeness_filter = completeness
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

        index = model.index(source_row, 0, source_parent)
        
        # 1. Filter by active status
        is_active = model.data(index, ACTIVE_STATUS_ROLE)
        if self._active_status == "active" and not is_active:
            return False
        if self._active_status == "archived" and is_active:
            return False

        # 2. Filter by search terms (AND logic)
        if self._search_terms:
            search_text = model.data(index, self.SEARCH_ROLE)
            if not search_text:
                return False
            search_lower = search_text.lower()
            if not all(term in search_lower for term in self._search_terms):
                return False

        # 3. Filter by country
        if self._country_filter:
            country = model.data(index, COUNTRY_ROLE) or ""
            if country.lower() != self._country_filter.lower():
                return False

        # 4. Filter by document completeness
        if self._completeness_filter != "all":
            completeness = model.data(index, COMPLETENESS_ROLE) or ""
            if completeness != self._completeness_filter:
                return False

        # 5. Filter by arrival date range
        if self._arrival_date_from or self._arrival_date_to:
            arrival_date = model.data(index, ARRIVAL_DATE_ROLE)
            if isinstance(arrival_date, str):
                arrival_date = QDate.fromString(arrival_date, Qt.ISODate)
            
            if arrival_date:
                if self._arrival_date_from and arrival_date < self._arrival_date_from:
                    return False
                if self._arrival_date_to and arrival_date > self._arrival_date_to:
                    return False

        # 6. Filter by created date range
        if self._created_date_from or self._created_date_to:
            created_date = model.data(index, CREATED_DATE_ROLE)
            if isinstance(created_date, str):
                created_date = QDate.fromString(created_date, Qt.ISODate)
            
            if created_date:
                if self._created_date_from and created_date < self._created_date_from:
                    return False
                if self._created_date_to and created_date > self._created_date_to:
                    return False

        return True

