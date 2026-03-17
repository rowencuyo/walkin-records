"""
Validation helpers for field-level data validation.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.constants import (
    ALLOWED_DOCUMENT_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS,
    PASSPORT_MIN_LENGTH, PASSPORT_MAX_LENGTH,
)


def validate_required(value: str, field_name: str) -> Optional[str]:
    """Return error message if value is empty, else None."""
    if not value or not value.strip():
        return f"{field_name} is required"
    return None


def validate_date(value: str, field_name: str = "Date") -> Optional[str]:
    """Validate YYYY-MM-DD format. Returns error or None."""
    if not value or not value.strip():
        return None  # Not required by this validator
    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
        return None
    except ValueError:
        return f"{field_name} must be in YYYY-MM-DD format"


def validate_date_required(value: str, field_name: str = "Date") -> Optional[str]:
    """Validate required YYYY-MM-DD date."""
    err = validate_required(value, field_name)
    if err:
        return err
    return validate_date(value, field_name)


def validate_passport(value: str) -> Optional[str]:
    """Validate passport number format (alphanumeric, 3-20 chars)."""
    if not value or not value.strip():
        return "Passport Number is required"
    v = value.strip()
    if not re.match(r"^[A-Za-z0-9\-]+$", v):
        return "Passport Number must contain only letters, numbers, and hyphens"
    if len(v) < PASSPORT_MIN_LENGTH or len(v) > PASSPORT_MAX_LENGTH:
        return f"Passport Number must be between {PASSPORT_MIN_LENGTH} and {PASSPORT_MAX_LENGTH} characters"
    return None


def validate_file_type(path: str, allowed: set[str] | None = None) -> Optional[str]:
    """Validate file extension against allowed set."""
    if allowed is None:
        allowed = ALLOWED_DOCUMENT_EXTENSIONS
    ext = Path(path).suffix.lower()
    if ext not in allowed:
        allowed_str = ", ".join(sorted(allowed))
        return f"File type '{ext}' is not allowed. Allowed: {allowed_str}"
    return None


def validate_file_size(path: str, max_bytes: int) -> Optional[str]:
    """Validate that file is within size limit."""
    p = Path(path)
    if not p.exists():
        return "File does not exist"
    size = p.stat().st_size
    if size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        actual_mb = size / (1024 * 1024)
        return f"File size ({actual_mb:.1f} MB) exceeds limit ({max_mb:.1f} MB)"
    return None


def validate_image_file(path: str) -> Optional[str]:
    """Validate that a file is a supported image format."""
    return validate_file_type(path, ALLOWED_IMAGE_EXTENSIONS)
