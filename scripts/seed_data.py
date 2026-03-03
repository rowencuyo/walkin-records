"""
Seed script to generate test data for performance verification.
Generates 10,000+ random walk-in records.
"""
import os
import sys
import random
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import initialize_database, get_connection
from app.constants import (
    Sex, VisaStatus, EducationalLevel, Semester,
    VISA_CATEGORIES, YEAR_LEVELS, COUNTRIES,
)
from app.utils.logger import setup_logging

setup_logging()

FIRST_NAMES = [
    "Ahmad", "Ali", "Amir", "Anh", "Arjun", "Binh", "Chen", "Dae", "Deepak", "Farhan",
    "Fatima", "Hana", "Haruto", "Ibrahim", "Jia", "Jin", "Karthik", "Kenji", "Khalid", "Kim",
    "Linh", "Mai", "Ming", "Mohammed", "Nadia", "Naomi", "Nguyen", "Noura", "Omar", "Priya",
    "Rahul", "Riko", "Sana", "Siti", "Suki", "Takeshi", "Thanh", "Wei", "Yuki", "Zara",
    "Abdul", "Aditi", "Akira", "Amara", "Ananya", "Bao", "Chandra", "Daisuke", "Elena", "Faisal",
]

LAST_NAMES = [
    "Abbas", "Abe", "Ahmed", "Bae", "Bautista", "Chand", "Choi", "Cruz", "Das", "Diaz",
    "Fang", "Garcia", "Gupta", "Ha", "Hassan", "Hayashi", "Hernandez", "Ho", "Huang", "Islam",
    "Ito", "Jain", "Kato", "Khan", "Kim", "Kumar", "Le", "Lee", "Li", "Lim",
    "Lopez", "Matsumoto", "Mirza", "Mori", "Nakamura", "Ngo", "Nguyen", "Osman", "Park", "Patel",
    "Phong", "Qureshi", "Rahman", "Ramos", "Santos", "Sato", "Shah", "Singh", "Suzuki", "Tan",
    "Tanaka", "Tran", "Wang", "Watanabe", "Wong", "Wu", "Yamada", "Yang", "Zhang", "Zhou",
]

MIDDLE_NAMES = [
    "", "", "", "A.", "B.", "C.", "D.", "De", "Del", "Dela",
    "E.", "F.", "G.", "H.", "J.", "K.", "L.", "M.", "N.", "P.",
]

COURSES = [
    "BS Computer Science", "BS Information Technology", "BS Nursing",
    "BS Business Administration", "BS Civil Engineering", "BS Architecture",
    "BS Pharmacy", "BS Medical Technology", "BS Hospitality Management",
    "BS Psychology", "BS Education", "BS Accountancy", "BS Biology",
    "BS Electrical Engineering", "BS Mechanical Engineering",
    "MA Education", "MA Business Administration", "MS Computer Science",
    "MS Engineering", "PhD Education", "PhD Computer Science",
    "BS Maritime Studies", "BS Tourism Management", "BS Criminology",
    "BS Agriculture", "BS Environmental Science",
]

STREETS = [
    "123 Rizal St", "456 Mabini Ave", "789 Bonifacio Blvd", "12 Quezon Drive",
    "34 Luna St", "56 Del Pilar Rd", "78 Aguinaldo Way", "90 Laurel Ave",
    "111 Magsaysay Blvd", "222 Osmeña Highway",
]

BARANGAYS = [
    "Poblacion", "San Miguel", "Santa Cruz", "San Jose", "San Antonio",
    "Santo Niño", "Bagong Silang", "Maharlika", "Bagumbayan", "Kamuning",
]

CITIES = [
    "Manila", "Quezon City", "Cebu City", "Davao City", "Makati",
    "Pasig", "Taguig", "Mandaluyong", "Caloocan", "Las Piñas",
    "Parañaque", "Pasay", "Marikina", "Muntinlupa", "Valenzuela",
]

PROVINCES = [
    "Metro Manila", "Cebu", "Davao del Sur", "Pampanga", "Bulacan",
    "Laguna", "Cavite", "Rizal", "Batangas", "Pangasinan",
]


def random_date(start_year=2015, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).strftime("%Y-%m-%d")


def random_passport():
    letter = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    nums = "".join(random.choices("0123456789", k=random.randint(6, 9)))
    return f"{letter}{nums}"


def seed(count=10000):
    print(f"Seeding {count} records...")
    initialize_database()
    conn = get_connection()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    used_passports = set()
    batch = []

    for i in range(count):
        passport = random_passport()
        while passport in used_passports:
            passport = random_passport()
        used_passports.add(passport)

        record = (
            random.choice(LAST_NAMES),                    # last_name
            random.choice(FIRST_NAMES),                   # first_name
            random.choice(MIDDLE_NAMES),                  # middle_name
            random.choice([s.value for s in Sex]),         # sex
            random_date(1970, 2005),                       # date_of_birth
            passport,                                      # passport_number
            random.choice(COUNTRIES),                      # country_of_citizenship
            random.choice(STREETS),                        # street
            random.choice(BARANGAYS),                      # barangay
            random.choice(CITIES),                         # city_municipality
            random.choice(PROVINCES),                      # province
            random_date(2018, 2025),                       # date_of_arrival
            random_date(2018, 2025),                       # date_start_education
            random.choice([el.value for el in EducationalLevel]),  # educational_level
            random.choice(COURSES),                        # course_program
            random.choice(YEAR_LEVELS),                    # year_level
            random.choice([s.value for s in Semester]),     # semester
            random.choice(VISA_CATEGORIES),                # visa_category
            random_date(2020, 2025),                       # visa_grant_date
            random_date(2025, 2028),                       # visa_validity_date
            random.choice([vs.value for vs in VisaStatus]),# visa_status
            "",                                            # remarks
            1 if random.random() > 0.05 else 0,           # is_active (95% active)
            now,                                           # created_at
            now,                                           # updated_at
        )
        batch.append(record)

        if len(batch) >= 1000:
            conn.executemany(
                """INSERT INTO walkin_records 
                   (last_name, first_name, middle_name, sex, date_of_birth,
                    passport_number, country_of_citizenship,
                    street, barangay, city_municipality, province,
                    date_of_arrival, date_start_education, educational_level,
                    course_program, year_level, semester,
                    visa_category, visa_grant_date, visa_validity_date,
                    visa_status, remarks, is_active, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                batch,
            )
            conn.commit()
            print(f"  Inserted {i + 1} records...")
            batch = []

    if batch:
        conn.executemany(
            """INSERT INTO walkin_records 
               (last_name, first_name, middle_name, sex, date_of_birth,
                passport_number, country_of_citizenship,
                street, barangay, city_municipality, province,
                date_of_arrival, date_start_education, educational_level,
                course_program, year_level, semester,
                visa_category, visa_grant_date, visa_validity_date,
                visa_status, remarks, is_active, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            batch,
        )
        conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM walkin_records").fetchone()[0]
    print(f"Done! Total records in database: {total}")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    seed(count)
