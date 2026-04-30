"""
Data models for the Walk-In Records Management System.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class WalkInRecord:
    """Represents a walk-in / student record."""
    # Identity
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    suffix_name: str = ""  # Jr., Sr., II, etc.
    sex: str = ""
    date_of_birth: str = ""  # YYYY-MM-DD
    passport_number: str = ""
    country_of_citizenship: str = ""

    # Philippine Residential Address
    street: str = ""
    barangay: str = ""
    city_municipality: str = ""
    province: str = ""
    region: str = ""  # Philippine region

    # Academic & Residency
    date_of_arrival: str = ""  # YYYY-MM-DD
    date_start_education: str = ""  # YYYY-MM-DD
    educational_level: str = ""
    course_program: str = ""
    year_level: str = ""
    semester: str = ""

    # Visa Information
    visa_category: str = ""
    visa_grant_date: str = ""  # YYYY-MM-DD
    visa_validity_date: str = ""  # YYYY-MM-DD
    visa_status: str = ""  # Within / Outside Philippines
    remarks: str = ""

    # Enrollment
    location_status: str = ""   # e.g. Within / Outside Philippines
    enrollment_status: str = ""  # Enrolled / Dropped / Graduated / etc.

    # System fields
    id: Optional[int] = None
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""

    @property
    def full_name(self) -> str:
        parts = [self.first_name, self.middle_name, self.last_name]
        name = " ".join(p for p in parts if p)
        if self.suffix_name:
            name = f"{name} {self.suffix_name}"
        return name

    @property
    def display_name(self) -> str:
        """Full name guaranteed to have no leading/trailing spaces."""
        return self.full_name.strip()

    def to_dict(self) -> dict:
        """Convert to dictionary for database operations."""
        return {
            "last_name": self.last_name,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "suffix_name": self.suffix_name,
            "sex": self.sex,
            "date_of_birth": self.date_of_birth,
            "passport_number": self.passport_number,
            "country_of_citizenship": self.country_of_citizenship,
            "street": self.street,
            "barangay": self.barangay,
            "city_municipality": self.city_municipality,
            "province": self.province,
            "region": self.region,
            "date_of_arrival": self.date_of_arrival,
            "date_start_education": self.date_start_education,
            "educational_level": self.educational_level,
            "course_program": self.course_program,
            "year_level": self.year_level,
            "semester": self.semester,
            "visa_category": self.visa_category,
            "visa_grant_date": self.visa_grant_date,
            "visa_validity_date": self.visa_validity_date,
            "visa_status": self.visa_status,
            "remarks": self.remarks,
            "location_status": self.location_status,
            "enrollment_status": self.enrollment_status,
            "is_active": 1 if self.is_active else 0,
        }

    @classmethod
    def from_row(cls, row: dict) -> "WalkInRecord":
        """Create a WalkInRecord from a database row dictionary."""
        return cls(
            id=row.get("id"),
            last_name=row.get("last_name", ""),
            first_name=row.get("first_name", ""),
            middle_name=row.get("middle_name", ""),
            suffix_name=row.get("suffix_name", ""),
            sex=row.get("sex", ""),
            date_of_birth=row.get("date_of_birth", ""),
            passport_number=row.get("passport_number", ""),
            country_of_citizenship=row.get("country_of_citizenship", ""),
            street=row.get("street", ""),
            barangay=row.get("barangay", ""),
            city_municipality=row.get("city_municipality", ""),
            province=row.get("province", ""),
            region=row.get("region", ""),
            date_of_arrival=row.get("date_of_arrival", ""),
            date_start_education=row.get("date_start_education", ""),
            educational_level=row.get("educational_level", ""),
            course_program=row.get("course_program", ""),
            year_level=row.get("year_level", ""),
            semester=row.get("semester", ""),
            visa_category=row.get("visa_category", ""),
            visa_grant_date=row.get("visa_grant_date", ""),
            visa_validity_date=row.get("visa_validity_date", ""),
            visa_status=row.get("visa_status", ""),
            remarks=row.get("remarks", ""),
            location_status=row.get("location_status", ""),
            enrollment_status=row.get("enrollment_status", ""),
            is_active=bool(row.get("is_active", 1)),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )


@dataclass
class Document:
    """Represents an uploaded document associated with a record."""
    id: Optional[int] = None
    record_id: int = 0
    document_type: str = ""
    file_path: str = ""
    file_name: str = ""
    file_type: str = ""
    file_size: int = 0
    upload_date: str = ""

    @classmethod
    def from_row(cls, row: dict) -> "Document":
        return cls(
            id=row.get("id"),
            record_id=row.get("record_id", 0),
            document_type=row.get("document_type", ""),
            file_path=row.get("file_path", ""),
            file_name=row.get("file_name", ""),
            file_type=row.get("file_type", ""),
            file_size=row.get("file_size", 0),
            upload_date=row.get("upload_date", ""),
        )


@dataclass
class ProfilePicture:
    """Represents a profile picture for a record."""
    id: Optional[int] = None
    record_id: int = 0
    file_path: str = ""
    upload_date: str = ""

    @classmethod
    def from_row(cls, row: dict) -> "ProfilePicture":
        return cls(
            id=row.get("id"),
            record_id=row.get("record_id", 0),
            file_path=row.get("file_path", ""),
            upload_date=row.get("upload_date", ""),
        )


@dataclass
class Notification:
    """Represents a system notification."""
    id: Optional[int] = None
    severity: str = "info"        # 'info', 'warning', 'critical'
    category: str = ""            # 'visa_expiry', 'missing_docs', 'backup', etc.
    title: str = ""
    message: str = ""
    group_key: str = ""
    record_id: Optional[int] = None
    status: str = "unread"        # 'unread', 'read', 'dismissed', 'resolved'
    created_at: str = ""
    resolved_at: str = ""

    @classmethod
    def from_row(cls, row: dict) -> "Notification":
        return cls(
            id=row.get("id"),
            severity=row.get("severity", "info"),
            category=row.get("category", ""),
            title=row.get("title", ""),
            message=row.get("message", ""),
            group_key=row.get("group_key", ""),
            record_id=row.get("record_id"),
            status=row.get("status", "unread"),
            created_at=row.get("created_at", ""),
            resolved_at=row.get("resolved_at", ""),
        )


@dataclass
class RecentActivity:
    """Represents a recent activity entry."""
    id: Optional[int] = None
    record_id: int = 0
    action: str = ""              # 'viewed', 'edited'
    timestamp: str = ""

    @classmethod
    def from_row(cls, row: dict) -> "RecentActivity":
        return cls(
            id=row.get("id"),
            record_id=row.get("record_id", 0),
            action=row.get("action", ""),
            timestamp=row.get("timestamp", ""),
        )
