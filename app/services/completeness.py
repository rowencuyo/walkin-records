"""
Record data completeness checking.
Determines if a record has all required fields and all required document types.
"""
from app.models import WalkInRecord
from app.constants import DocumentType

# Fields that must be non-empty for a record to be considered complete
REQUIRED_FIELDS = [
    ("last_name", "Last Name"),
    ("first_name", "First Name"),
    ("sex", "Sex"),
    ("date_of_birth", "Date of Birth"),
    ("passport_number", "Passport Number"),
    ("country_of_citizenship", "Country of Citizenship"),
]

# All 5 document types must be uploaded
REQUIRED_DOCUMENT_TYPES = [dt.value for dt in DocumentType]


def check_completeness(
    record: WalkInRecord,
    document_count: int = 0,
    document_types: list[str] | None = None,
) -> tuple[str, list[str]]:
    """
    Check record completeness.

    Args:
        record: The record to check.
        document_count: Total number of documents uploaded.
        document_types: List of document type strings that have been uploaded.

    Returns:
        (status, missing_items) where status is one of:
        - "complete"
        - "missing_fields"
        - "no_documents"
        - "incomplete_documents"
    """
    missing = []

    # Check required fields
    for field_key, field_label in REQUIRED_FIELDS:
        value = getattr(record, field_key, "")
        if not value or not str(value).strip():
            missing.append(f"Field: {field_label}")

    if missing:
        return "missing_fields", missing

    # Check all 5 required document types are uploaded
    uploaded = set(document_types or [])
    missing_docs = [dt for dt in REQUIRED_DOCUMENT_TYPES if dt not in uploaded]
    if missing_docs:
        if document_count == 0:
            return "no_documents", [f"Document: {dt}" for dt in missing_docs]
        else:
            return "incomplete_documents", [f"Document: {dt}" for dt in missing_docs]

    return "complete", []
