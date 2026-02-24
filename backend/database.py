from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "database.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Fix for Heroku/Render postgres:// -> postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Automatically create tables on startup."""
    url_for_log = str(DATABASE_URL)[:30] if DATABASE_URL else "None"
    print(f"📡 Initializing Database: {url_for_log}...")
    with engine.connect() as conn:
        tables = [
            """
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                student_code TEXT UNIQUE NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                course_name TEXT NOT NULL,
                course_code TEXT UNIQUE NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                attendance_date DATE NOT NULL,
                check_in_time TIME NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT CHECK(status IN ('Present', 'Absent', 'Late')),
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                UNIQUE(student_id, course_id, attendance_date)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS grades (
                id SERIAL PRIMARY KEY,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                term1 REAL NOT NULL,
                term2 REAL NOT NULL,
                term3 REAL NOT NULL,
                attendance_score REAL NOT NULL,
                final_passed INTEGER NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE,
                UNIQUE(student_id, course_id)
            )
            """
        ]
        for table_sql in tables:
            # Handle SQLite vs PostgreSQL differences
            sql = table_sql
            if DATABASE_URL.startswith("sqlite"):
                sql = sql.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
            conn.execute(text(sql))
        
        # Ensure at least one course exists for CSV imports
        conn.execute(text("""
            INSERT INTO courses (id, course_name, course_code)
            VALUES (1, 'General Analytics', 'GEN101')
            ON CONFLICT (id) DO NOTHING
        """))
        
        conn.commit()
    print("✅ Database initialized successfully.")