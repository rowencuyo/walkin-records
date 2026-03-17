"""
Seed script: populates 2000 dummy records with profile pictures and documents.
Run from project root: py seed_data.py
"""
import os
import sys
import random
import string
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# ── Project setup ──
_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))

from app.database import get_connection, initialize_database, DATA_DIR, DOCUMENTS_DIR, PROFILE_PICS_DIR

# ── Config ──
NUM_RECORDS = 500

# ── Data pools ──
FIRST_NAMES_M = [
    "James", "John", "Robert", "Michael", "David", "William", "Richard", "Joseph", "Thomas",
    "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven",
    "Andrew", "Paul", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy",
    "Ahmed", "Mohammed", "Wei", "Hiroshi", "Raj", "Sanjay", "Omar", "Yusuf", "Jin",
    "Carlos", "Diego", "Luis", "Pedro", "Hassan", "Ali", "Nguyen", "Tran", "Kim",
    "Takeshi", "Ryu", "Sato", "Park", "Choi", "Lee", "Chen", "Zhang", "Li",
]
FIRST_NAMES_F = [
    "Mary", "Patricia", "Jennifer", "Linda", "Barbara", "Elizabeth", "Susan", "Jessica",
    "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley",
    "Emily", "Donna", "Michelle", "Dorothy", "Carol", "Amanda", "Melissa", "Deborah",
    "Fatima", "Aisha", "Mei", "Yuki", "Priya", "Sunita", "Layla", "Amira", "Hana",
    "Maria", "Ana", "Rosa", "Carmen", "Linh", "Thanh", "Sakura", "Min", "Soo",
    "Yuna", "Haruka", "Ji", "Hyun", "Xia", "Ling", "Fang", "Wen",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White",
    "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Hall",
    "Khan", "Patel", "Singh", "Kumar", "Wang", "Chen", "Li", "Zhang", "Liu",
    "Nguyen", "Tran", "Pham", "Kim", "Park", "Choi", "Yamamoto", "Tanaka", "Sato",
    "Santos", "Rivera", "Cruz", "Reyes",  "Morales", "Del Rosario", "Bautista",
    "Al-Rashid", "Al-Farsi", "Ibrahim", "Hassan", "Okafor", "Adeyemi", "Mensah",
]
MIDDLE_NAMES = [
    "", "", "", "", "",  # 50% chance of no middle name
    "A.", "B.", "C.", "D.", "E.", "G.", "J.", "K.", "L.", "M.", "N.", "P.", "R.", "S.", "T.",
    "Marie", "Rose", "Anne", "May", "Grace", "Jay", "Ray", "Cole", "Cruz",
]
COUNTRIES = [
    "China", "India", "South Korea", "Japan", "Vietnam", "Indonesia", "Thailand",
    "Malaysia", "Bangladesh", "Pakistan", "Nepal", "Myanmar", "Cambodia",
    "Nigeria", "Ghana", "Kenya", "South Africa", "Egypt", "Ethiopia",
    "United States", "Canada", "United Kingdom", "Australia", "Germany", "France",
    "Brazil", "Mexico", "Colombia", "Argentina", "Peru",
    "Saudi Arabia", "United Arab Emirates", "Iran", "Iraq", "Turkey",
    "Russia", "Ukraine", "Taiwan", "Singapore", "Sri Lanka",
]
COURSES = [
    "Computer Science", "Information Technology", "Nursing", "Business Administration",
    "Mechanical Engineering", "Civil Engineering", "Electrical Engineering", "Architecture",
    "Education", "Psychology", "Biology", "Chemistry", "Mathematics", "Physics",
    "Accounting", "Finance", "Marketing", "Tourism Management", "Hospitality Management",
    "Medicine", "Dentistry", "Pharmacy", "Public Health", "Environmental Science",
    "Political Science", "Sociology", "Communication Arts", "Journalism",
    "Fine Arts", "Music", "Philosophy", "Law",
]
EDU_LEVELS = ["Elementary", "Junior High School", "Senior High School", "Undergraduate", "Graduate", "Post-Graduate"]
YEAR_LEVELS = ["1st Year", "2nd Year", "3rd Year", "4th Year", "5th Year", "6th Year", "Graduate"]
SEMESTERS = ["1st Semester", "2nd Semester", "Summer"]
VISA_CATEGORIES = [
    "9(a) - Temporary Visitor", "9(d) - Treaty Trader / Investor", "9(f) - Student Visa",
    "9(g) - Pre-arranged Employment", "47(a)(2) - Special Non-Immigrant",
    "EO 324 - Foreign Students", "SSP - Special Study Permit", "Other",
]
VISA_STATUSES = ["Within the Philippines", "Outside the Philippines"]
ENROLLMENT_STATUSES = ["Enrolled", "Dropped", "Graduated"]
SUFFIXES = ["", "", "", "", "", "", "Jr.", "Sr.", "II", "III"]
REGIONS = [
    "NCR - National Capital Region", "CAR - Cordillera Administrative Region",
    "Region I - Ilocos Region", "Region III - Central Luzon",
    "Region IV-A - CALABARZON", "Region VII - Central Visayas",
    "Region XI - Davao Region",
]
CITIES = [
    "Manila", "Quezon City", "Makati", "Cebu City", "Davao City", "Baguio",
    "Pasig", "Taguig", "Caloocan", "Antipolo", "Iloilo City", "Bacolod",
]
BARANGAYS = ["Brgy. 1", "Brgy. San Jose", "Brgy. Poblacion", "Brgy. Pag-asa", "Brgy. Maligaya", "Brgy. Rizal"]
PROVINCES = ["Metro Manila", "Cebu", "Davao del Sur", "Pampanga", "Bulacan", "Laguna", "Batangas", "Cavite"]
DOC_TYPES = ["Passport", "Birth Certificate", "Graduation Certificate", "Good Moral Certificate", "Bank Statement"]


def _random_date(start_year, end_year):
    """Return a random YYYY-MM-DD date string."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    d = start + timedelta(days=random.randint(0, delta))
    return d.strftime("%Y-%m-%d")


def _random_passport():
    """Generate a random passport-like string."""
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    digits = "".join(random.choices(string.digits, k=7))
    return f"{letters}{digits}"


def _make_dummy_image(path: Path, record_id: int):
    """Create a small colored PNG image as a dummy profile picture."""
    # Generate a minimal valid PNG file (1x1 pixel)
    # Using a colored square to be visible
    import struct, zlib
    width, height = 64, 64
    r = random.randint(60, 220)
    g = random.randint(60, 220)
    b = random.randint(60, 220)
    # Build raw pixel data
    raw_data = b""
    for y in range(height):
        raw_data += b"\x00"  # filter byte
        for x in range(width):
            raw_data += bytes([r, g, b])
    compressed = zlib.compress(raw_data)

    def _chunk(chunk_type, data):
        c = chunk_type + data
        crc = zlib.crc32(c) & 0xffffffff
        return struct.pack(">I", len(data)) + c + struct.pack(">I", crc)

    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", compressed)
    png += _chunk(b"IEND", b"")

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


def _make_dummy_document(path: Path):
    """Create a minimal PDF file as a dummy document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Minimal valid PDF
    pdf_content = b"""%PDF-1.0
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
206
%%EOF"""
    with open(path, "wb") as f:
        f.write(pdf_content)


def seed():
    print(f"Initializing database...")
    initialize_database()
    conn = get_connection()

    # Check how many records already exist
    existing = conn.execute("SELECT COUNT(*) FROM walkin_records").fetchone()[0]
    print(f"Existing records: {existing}")
    print(f"Inserting {NUM_RECORDS} dummy records...")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i in range(1, NUM_RECORDS + 1):
        sex = random.choice(["Male", "Female"])
        first = random.choice(FIRST_NAMES_M if sex == "Male" else FIRST_NAMES_F)
        last = random.choice(LAST_NAMES)
        middle = random.choice(MIDDLE_NAMES)
        suffix = random.choice(SUFFIXES)
        dob = _random_date(1980, 2005)
        passport = _random_passport()
        country = random.choice(COUNTRIES)
        arrival = _random_date(2018, 2025)
        start_edu = _random_date(2019, 2025)
        edu_level = random.choice(EDU_LEVELS)
        course = random.choice(COURSES)
        year = random.choice(YEAR_LEVELS)
        semester = random.choice(SEMESTERS)
        visa_cat = random.choice(VISA_CATEGORIES)
        visa_grant = _random_date(2019, 2025)
        visa_validity = _random_date(2025, 2028)
        visa_status = random.choice(VISA_STATUSES)
        enrollment = random.choice(ENROLLMENT_STATUSES)
        region = random.choice(REGIONS)
        city = random.choice(CITIES)
        barangay = random.choice(BARANGAYS)
        province = random.choice(PROVINCES)
        street = f"{random.randint(1, 999)} {random.choice(['Main St', 'Rizal Ave', 'Mabini St', 'Del Pilar St', 'Bonifacio Rd', 'Luna St'])}"
        created = _random_date(2023, 2025) + " " + f"{random.randint(8,17):02d}:{random.randint(0,59):02d}:00"

        # 10% chance of expired visa
        if random.random() < 0.1:
            visa_validity = _random_date(2023, 2025)

        cursor = conn.execute(
            """INSERT INTO walkin_records (
                last_name, first_name, middle_name, suffix_name, sex, date_of_birth,
                passport_number, country_of_citizenship,
                street, barangay, city_municipality, province, region,
                date_of_arrival, date_start_education, educational_level,
                course_program, year_level, semester,
                visa_category, visa_grant_date, visa_validity_date, visa_status,
                enrollment_status, remarks, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                last, first, middle, suffix, sex, dob, passport, country,
                street, barangay, city, province, region,
                arrival, start_edu, edu_level, course, year, semester,
                visa_cat, visa_grant, visa_validity, visa_status,
                enrollment, "", 1, created, created,
            ),
        )
        record_id = cursor.lastrowid

        # ── Profile picture (80% chance) ──
        if random.random() < 0.8:
            pic_filename = f"{record_id}.png"
            pic_path = PROFILE_PICS_DIR / pic_filename
            _make_dummy_image(pic_path, record_id)
            conn.execute(
                "INSERT INTO profile_pictures (record_id, file_path, upload_date) VALUES (?, ?, ?)",
                (record_id, str(pic_path), now_str),
            )

        # ── Documents (1-4 random types) ──
        num_docs = random.randint(0, 4)
        chosen_types = random.sample(DOC_TYPES, min(num_docs, len(DOC_TYPES)))
        for doc_type in chosen_types:
            doc_filename = f"{record_id}_{doc_type.replace(' ', '_').lower()}.pdf"
            doc_dir = DOCUMENTS_DIR / str(record_id)
            doc_path = doc_dir / doc_filename
            _make_dummy_document(doc_path)
            file_size = doc_path.stat().st_size
            conn.execute(
                """INSERT INTO documents (record_id, document_type, file_path, file_name, file_type, file_size, upload_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (record_id, doc_type, str(doc_path), doc_filename, "application/pdf", file_size, now_str),
            )

        if i % 200 == 0:
            conn.commit()
            print(f"  ... inserted {i}/{NUM_RECORDS}")

    conn.commit()
    final = conn.execute("SELECT COUNT(*) FROM walkin_records").fetchone()[0]
    pics = conn.execute("SELECT COUNT(*) FROM profile_pictures").fetchone()[0]
    docs = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    print(f"\nDone! Total records: {final}, Profile pics: {pics}, Documents: {docs}")


if __name__ == "__main__":
    seed()
