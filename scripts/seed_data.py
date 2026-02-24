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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            term1 REAL NOT NULL,
            term2 REAL NOT NULL,
            term3 REAL NOT NULL,
            attendance_score REAL NOT NULL,
            final_passed INTEGER NOT NULL, -- 1 for Pass, 0 for Fail
            FOREIGN KEY (student_id) REFERENCES students (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            UNIQUE(student_id, course_id)
        )
    ''')

def insert_sample_data(cursor):
    """Inserts sample records into students, courses, attendance, and grades."""
    print("Inserting sample data...")
    import random

    # Sample Students
    students = [
        ('Alice Johnson', 'alice@example.com', 'S101'),
        ('Bob Smith', 'bob@example.com', 'S102'),
        ('Charlie Brown', 'charlie@example.com', 'S103'),
        ('Diana Prince', 'diana@example.com', 'S104'),
        ('Ethan Hunt', 'ethan@example.com', 'S105'),
        ('Fiona Gallagher', 'fiona@example.com', 'S106')
    ]
    cursor.executemany('INSERT OR IGNORE INTO students (name, email, student_code) VALUES (?, ?, ?)', students)

    # Sample Courses
    courses = [
        ('Mathematics 101', 'MATH101'),
        ('Physics 202', 'PHYS202'),
        ('Computer Science 303', 'CS303')
    ]
    cursor.executemany('INSERT OR IGNORE INTO courses (course_name, course_code) VALUES (?, ?)', courses)

    # Fetch IDs
    cursor.execute('SELECT id FROM students ORDER BY student_code')
    student_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute('SELECT id FROM courses ORDER BY course_code')
    course_ids = [row[0] for row in cursor.fetchall()]

    # Sample Attendance (Multiple days for variety)
    print("Generating attendance and grades...")
    dates = ['2026-02-20', '2026-02-21', '2026-02-22']
    
    for s_id in student_ids:
        for c_id in course_ids:
            # Generate random attendance for the 3 days
            total_present = 0
            for d in dates:
                status = random.choice(['Present', 'Present', 'Present', 'Late', 'Absent'])
                if status in ['Present', 'Late']:
                    total_present += 1
                cursor.execute('''
                    INSERT OR IGNORE INTO attendance (student_id, course_id, attendance_date, check_in_time, status) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (s_id, c_id, d, '09:00:00', status))
            
            # Attendance Score (Percentage)
            att_score = (total_present / len(dates)) * 100
            
            # Generate wider random Term Marks (Term 1, 2, 3) to ensure some fails
            t1 = random.uniform(10, 95)
            t2 = random.uniform(10, 95)
            t3 = random.uniform(10, 95)
            
            # Pass/Fail Logic: (T1*0.2 + T2*0.2 + T3*0.4 + Attendance*0.2) >= 60
            final_score = (t1 * 0.2) + (t2 * 0.2) + (t3 * 0.4) + (att_score * 0.2)
            passed = 1 if final_score >= 60 else 0 
            
            cursor.execute('''
                INSERT OR IGNORE INTO grades (student_id, course_id, term1, term2, term3, attendance_score, final_passed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (s_id, c_id, t1, t2, t3, att_score, passed))

def run_test_queries(cursor):
    """Executes verification queries to show the state of the database."""
    print("\n--- Testing Queries ---")
    
    print("\nStudent Predicted Pass/Fail (based on Grades + Attendance):")
    cursor.execute('''
        SELECT s.name, c.course_name, g.term1, g.term2, g.term3, g.attendance_score, g.final_passed
        FROM grades g
        JOIN students s ON g.student_id = s.id
        JOIN courses c ON g.course_id = c.id
        LIMIT 10
    ''')
    for row in cursor.fetchall():
        status = "PASS" if row['final_passed'] == 1 else "FAIL"
        print(f"{row['name']} | {row['course_name']} | T1: {row['term1']:.1f}, T2: {row['term2']:.1f}, T3: {row['term3']:.1f} | Att: {row['attendance_score']:.1f}% | Result: {status}")

def seed_database():
    """Main function to orchestrate the seeding process."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        print(f"Connecting to database at: {DB_PATH}")
        create_tables(cursor)
        insert_sample_data(cursor)
        conn.commit()
        print("Database seeded successfully with Grades and Attendance data!")
        
        run_test_queries(cursor)
    except sqlite3.Error as e:
        print(f"Error seeding database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
