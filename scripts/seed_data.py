import sys
import os
# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine
from sqlalchemy import text
from datetime import datetime
import random

def create_tables(conn):
    """Creates the necessary tables using the shared engine."""
    print("Creating tables...")
    
    # SQLite uses AUTOINCREMENT, Postgres uses SERIAL/IDENTITY. 
    # For raw SQL portability in this seed script, we'll avoid AUTOINCREMENT 
    # and let the DB handle IDs if possible, or use simple INTEGER PRIMARY KEY.
    
    tables = [
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            student_code TEXT UNIQUE NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY,
            course_name TEXT NOT NULL,
            course_code TEXT UNIQUE NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            check_in_time TIME NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('Present', 'Absent', 'Late')),
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            UNIQUE(student_id, course_id, attendance_date)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            term1 REAL NOT NULL,
            term2 REAL NOT NULL,
            term3 REAL NOT NULL,
            attendance_score REAL NOT NULL,
            final_passed INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            UNIQUE(student_id, course_id)
        )
        """
    ]
    
    for table_sql in tables:
        # PostgreSQL doesn't like INTEGER PRIMARY KEY for autoidentities as much as SERIAL,
        # but for this specific seed script, we'll keep it simple or use ORM if we really wanted portability.
        # Since we are using raw SQL, we'll use a slightly safer syntax.
        sql = table_sql.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        conn.execute(text(sql))

def insert_sample_data(conn):
    """Inserts sample records using parameters to avoid injection and remain portable."""
    print("Inserting sample data...")

    # Sample Students
    students = [
        {'n': 'Alice Johnson', 'e': 'alice@example.com', 'c': 'S101'},
        {'n': 'Bob Smith', 'e': 'bob@example.com', 'c': 'S102'},
        {'n': 'Charlie Brown', 'e': 'charlie@example.com', 'c': 'S103'},
        {'n': 'Diana Prince', 'e': 'diana@example.com', 'c': 'S104'},
        {'n': 'Ethan Hunt', 'e': 'ethan@example.com', 'c': 'S105'},
        {'n': 'Fiona Gallagher', 'e': 'fiona@example.com', 'c': 'S106'}
    ]
    for s in students:
        conn.execute(text("""
            INSERT INTO students (name, email, student_code) 
            VALUES (:n, :e, :c) 
            ON CONFLICT (student_code) DO NOTHING
        """), s)

    # Sample Courses
    courses = [
        {'n': 'Mathematics 101', 'c': 'MATH101'},
        {'n': 'Physics 202', 'c': 'PHYS202'},
        {'n': 'Computer Science 303', 'c': 'CS303'}
    ]
    for c in courses:
        conn.execute(text("""
            INSERT INTO courses (course_name, course_code) 
            VALUES (:n, :c) 
            ON CONFLICT (course_code) DO NOTHING
        """), c)

    # Fetch IDs
    student_ids = [r[0] for r in conn.execute(text("SELECT id FROM students ORDER BY student_code")).fetchall()]
    course_ids = [r[0] for r in conn.execute(text("SELECT id FROM courses ORDER BY course_code")).fetchall()]

    # Sample Attendance
    print("Generating attendance and grades...")
    dates = ['2026-02-20', '2026-02-21', '2026-02-22']
    
    for s_id in student_ids:
        for c_id in course_ids:
            total_present = 0
            for d in dates:
                status = random.choice(['Present', 'Present', 'Present', 'Late', 'Absent'])
                if status in ['Present', 'Late']:
                    total_present += 1
                conn.execute(text("""
                    INSERT INTO attendance (student_id, course_id, attendance_date, check_in_time, status) 
                    VALUES (:s, :c, :d, :t, :st)
                    ON CONFLICT(student_id, course_id, attendance_date) DO NOTHING
                """), {'s': s_id, 'c': c_id, 'd': d, 't': '09:00:00', 'st': status})
            
            att_score = (total_present / len(dates)) * 100
            t1, t2, t3 = random.uniform(10, 95), random.uniform(10, 95), random.uniform(10, 95)
            final_score = (t1 * 0.2) + (t2 * 0.2) + (t3 * 0.4) + (att_score * 0.2)
            passed = 1 if final_score >= 60 else 0 
            
            conn.execute(text("""
                INSERT INTO grades (student_id, course_id, term1, term2, term3, attendance_score, final_passed)
                VALUES (:s, :c, :t1, :t2, :t3, :att, :p)
                ON CONFLICT(student_id, course_id) DO NOTHING
            """), {'s': s_id, 'c': c_id, 't1': t1, 't2': t2, 't3': t3, 'att': att_score, 'p': passed})

def run_test_queries(conn):
    print("\n--- Testing Queries ---")
    res = conn.execute(text("""
        SELECT s.name, c.course_name, g.term1, g.term2, g.term3, g.attendance_score, g.final_passed
        FROM grades g
        JOIN students s ON g.student_id = s.id
        JOIN courses c ON g.course_id = c.id
        LIMIT 10
    """)).fetchall()
    for row in res:
        status = "PASS" if row[6] == 1 else "FAIL"
        print(f"{row[0]} | {row[1]} | T1: {row[2]:.1f}, T2: {row[3]:.1f}, T3: {row[4]:.1f} | Att: {row[5]:.1f}% | Result: {status}")

def seed_database():
    with engine.connect() as conn:
        try:
            create_tables(conn)
            insert_sample_data(conn)
            conn.commit()
            print("Database seeded successfully!")
            run_test_queries(conn)
        except Exception as e:
            print(f"Error seeding: {e}")
            conn.rollback()

if __name__ == "__main__":
    seed_database()
