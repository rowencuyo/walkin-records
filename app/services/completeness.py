"""
Record data completeness checking.
Determines if a record has all required fields and documents.
"""
from app.models import WalkInRecord

# Fields that must be non-empty for a record to be considered complete
REQUIRED_FIELDS = [
    ("last_name", "Last Name"),
    ("first_name", "First Name"),
    ("sex", "Sex"),
    ("date_of_birth", "Date of Birth"),
    ("passport_number", "Passport Number"),
    ("country_of_citizenship", "Country of Citizenship"),
]


def check_completeness(
    record: WalkInRecord, document_count: int = 0
) -> tuple[str, list[str]]:
    """
    Check record completeness.

    Returns:
        (status, missing_items) where status is one of:
        - "complete"
        - "missing_fields"
        - "missing_documents"
    """
    missing = []

    # Check required fields
    for field_key, field_label in REQUIRED_FIELDS:
        value = getattr(record, field_key, "")
        if not value or not str(value).strip():
            missing.append(f"Field: {field_label}")

    if missing:
        return "missing_fields", missing

    # Check required documents (at least one document uploaded)
    if document_count == 0:
        return "missing_documents", ["No documents uploaded"]

    return "complete", []
