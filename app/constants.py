"""
Application constants, enumerations, and configuration values.
"""
from enum import Enum


class Sex(str, Enum):
    MALE = "Male"
    FEMALE = "Female"


class VisaStatus(str, Enum):
    WITHIN_PH = "Within the Philippines"
    OUTSIDE_PH = "Outside the Philippines"


class EducationalLevel(str, Enum):
    ELEMENTARY = "Elementary"
    JUNIOR_HIGH = "Junior High School"
    SENIOR_HIGH = "Senior High School"
    UNDERGRADUATE = "Undergraduate"
    GRADUATE = "Graduate"
    POST_GRADUATE = "Post-Graduate"


class Semester(str, Enum):
    FIRST = "1st Semester"
    SECOND = "2nd Semester"
    SUMMER = "Summer"


class EnrollmentStatus(str, Enum):
    ENROLLED = "Enrolled"
    DROPPED = "Dropped"
    GRADUATED = "Graduated"


SUFFIX_NAMES = ["", "Jr.", "Sr.", "II", "III", "IV", "V"]

PH_REGIONS = [
    "NCR - National Capital Region",
    "CAR - Cordillera Administrative Region",
    "Region I - Ilocos Region",
    "Region II - Cagayan Valley",
    "Region III - Central Luzon",
    "Region IV-A - CALABARZON",
    "MIMAROPA Region",
    "Region V - Bicol Region",
    "Region VI - Western Visayas",
    "Region VII - Central Visayas",
    "Region VIII - Eastern Visayas",
    "Region IX - Zamboanga Peninsula",
    "Region X - Northern Mindanao",
    "Region XI - Davao Region",
    "Region XII - SOCCSKSARGEN",
    "Region XIII - Caraga",
    "BARMM - Bangsamoro Autonomous Region",
]


class DocumentType(str, Enum):
    PASSPORT = "Passport"
    BIRTH_CERTIFICATE = "Birth Certificate"
    GRADUATION_CERTIFICATE = "Graduation Certificate"
    GOOD_MORAL_CERTIFICATE = "Good Moral Certificate"
    BANK_STATEMENT = "Bank Statement"


# Visa categories commonly used
VISA_CATEGORIES = [
    "9(a) - Temporary Visitor",
    "9(d) - Treaty Trader / Investor",
    "9(f) - Student Visa",
    "9(g) - Pre-arranged Employment",
    "47(a)(2) - Special Non-Immigrant",
    "EO 324 - Foreign Students",
    "RA 7919 - SIRV",
    "RA 9225 - Dual Citizenship",
    "SSP - Special Study Permit",
    "SWP - Special Work Permit",
    "Other",
]

YEAR_LEVELS = [
    "1st Year",
    "2nd Year",
    "3rd Year",
    "4th Year",
    "5th Year",
    "6th Year",
    "Graduate",
    "Other",
]

# File constraints
ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
MAX_DOCUMENT_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_PROFILE_PIC_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

# Pagination
DEFAULT_PAGE_SIZE = 50
PAGE_SIZE_OPTIONS = [25, 50, 100, 200]

# Search debounce
SEARCH_DEBOUNCE_MS = 200

# Countries (subset commonly needed)
COUNTRIES = [
    "Afghanistan", "Algeria", "Angola", "Argentina", "Australia",
    "Bangladesh", "Bhutan", "Brazil", "Brunei", "Cambodia",
    "Cameroon", "Canada", "Chad", "China", "Colombia",
    "Democratic Republic of the Congo", "East Timor", "Egypt", "Ethiopia",
    "France", "Germany", "Ghana", "India", "Indonesia",
    "Iran", "Iraq", "Israel", "Italy", "Japan",
    "Jordan", "Kazakhstan", "Kenya", "Kuwait", "Laos",
    "Lebanon", "Libya", "Madagascar", "Malaysia", "Mali",
    "Mexico", "Mongolia", "Morocco", "Mozambique", "Myanmar",
    "Nepal", "Netherlands", "New Zealand", "Niger", "Nigeria",
    "North Korea", "Oman", "Pakistan", "Palestine", "Papua New Guinea",
    "Peru", "Philippines", "Qatar", "Russia", "Rwanda",
    "Saudi Arabia", "Senegal", "Singapore", "Somalia", "South Africa",
    "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan",
    "Sweden", "Switzerland", "Syria", "Taiwan", "Tanzania",
    "Thailand", "Tunisia", "Turkey", "Uganda", "Ukraine",
    "United Arab Emirates", "United Kingdom", "United States", "Uzbekistan",
    "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe",
    "Other",
]


# ── v1.2: Notification Enums ──

class NotificationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class NotificationCategory(str, Enum):
    VISA_EXPIRY = "visa_expiry"
    VISA_EXPIRING = "visa_expiring"
    MISSING_DOCS = "missing_docs"
    BACKUP_OVERDUE = "backup_overdue"


class NotificationStatus(str, Enum):
    UNREAD = "unread"
    READ = "read"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"


# ── v1.2: Preference Defaults ──

DEFAULT_PREFERENCES = {
    "idle_lock_enabled": "false",
    "idle_lock_timeout_min": "15",
    "notify_visa_expiry": "true",
    "visa_expiry_threshold_days": "30",
    "notify_missing_docs": "true",
    "notify_backup_reminder": "true",
    "notification_retention_days": "90",
}

AUTO_LOCK_TIMEOUT_OPTIONS = [5, 10, 15, 30, 60]  # minutes
