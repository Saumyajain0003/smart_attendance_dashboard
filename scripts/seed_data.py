import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'database.db')

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable row-based access
    return conn

def create_tables(cursor):
    """Creates the necessary tables for students, courses, and attendance."""
    print("Creating tables...")
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            student_code TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_name TEXT NOT NULL,
            course_code TEXT UNIQUE NOT NULL
        )
    ''')

    # Improvement 2: Separate 'date' for easier analysis
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            check_in_time TIME NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('Present', 'Absent', 'Late')),
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            -- Improvement 4: Idempotency - prevent multiple logs for same student/course/date
            UNIQUE(student_id, course_id, attendance_date)
        )
    ''')

def insert_sample_data(cursor):
    """Inserts sample records into students, courses, and attendance tables."""
    print("Inserting sample data...")

    # Sample Students
    students = [
        ('Alice Johnson', 'alice@example.com', 'S101'),
        ('Bob Smith', 'bob@example.com', 'S102'),
        ('Charlie Brown', 'charlie@example.com', 'S103'),
        ('Diana Prince', 'diana@example.com', 'S104')
    ]
    cursor.executemany('INSERT OR IGNORE INTO students (name, email, student_code) VALUES (?, ?, ?)', students)

    # Sample Courses
    courses = [
        ('Mathematics 101', 'MATH101'),
        ('Physics 202', 'PHYS202'),
        ('Computer Science 303', 'CS303')
    ]
    cursor.executemany('INSERT OR IGNORE INTO courses (course_name, course_code) VALUES (?, ?)', courses)

    # Improvement 3: Deterministic data selection using ORDER BY
    cursor.execute('SELECT id FROM students ORDER BY student_code')
    student_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT id FROM courses ORDER BY course_code')
    course_ids = [row[0] for row in cursor.fetchall()]

    # Sample Attendance
    if student_ids and course_ids:
        # Use a fixed date for deterministic seeding
        fixed_date = '2026-02-22'
        
        attendance_records = [
            (student_ids[0], course_ids[0], fixed_date, '09:00:00', 'Present'),
            (student_ids[1], course_ids[0], fixed_date, '09:05:00', 'Late'),
            (student_ids[2], course_ids[0], fixed_date, '09:00:00', 'Present'),
            (student_ids[0], course_ids[1], fixed_date, '11:00:00', 'Present'),
            (student_ids[3], course_ids[1], fixed_date, '11:10:00', 'Late'),
            (student_ids[1], course_ids[2], fixed_date, '14:00:00', 'Present')
        ]
        # Use INSERT OR IGNORE for idempotency
        cursor.executemany('''
            INSERT OR IGNORE INTO attendance (student_id, course_id, attendance_date, check_in_time, status) 
            VALUES (?, ?, ?, ?, ?)
        ''', attendance_records)

def run_test_queries(cursor):
    """Executes verification queries to show the state of the database."""
    print("\n--- Testing Queries ---")
    
    print("\nRecent Attendance Logs:")
    cursor.execute('''
        SELECT s.name, c.course_name, a.attendance_date, a.check_in_time, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN courses c ON a.course_id = c.id
        ORDER BY a.attendance_date DESC, a.check_in_time DESC
    ''')
    for row in cursor.fetchall():
        print(f"{row['name']} | {row['course_name']} | {row['attendance_date']} {row['check_in_time']} | {row['status']}")

    print("\nStudent Count per Course:")
    cursor.execute('''
        SELECT c.course_name, COUNT(a.student_id) as student_count
        FROM attendance a
        JOIN courses c ON a.course_id = c.id
        GROUP BY c.course_name
    ''')
    for row in cursor.fetchall():
        print(f"{row['course_name']}: {row['student_count']} students")

    print("\nStudents below threshold:")
    cursor.execute('''
    SELECT 
        s.id,
        s.name,
        s.student_code,
        COUNT(a.id) AS total_classes,
        SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
        ROUND(
            (SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0) / COUNT(a.id),
            2
        ) AS attendance_percentage
    FROM students s
    JOIN attendance a ON s.id = a.student_id
    GROUP BY s.id
    HAVING attendance_percentage < 75;
    ''')
    for row in cursor.fetchall():
        print(f"{row['name']} | {row['attendance_percentage']} attendance")

def seed_database():
    """Main function to orchestrate the seeding process."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print(f"Connecting to database at: {DB_PATH}")
        create_tables(cursor)
        insert_sample_data(cursor)
        conn.commit()
        print("Database seeded successfully!")
        
        run_test_queries(cursor)
    except sqlite3.Error as e:
        print(f"Error seeding database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
