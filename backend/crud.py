from sqlalchemy.orm import Session
from sqlalchemy import text

def get_students_at_risk(db: Session, attendance_threshold: int = 75, grade_threshold: int = 50):
    query = text("""
        SELECT 
            s.id AS student_id,
            s.name,
            s.student_code,
            g.attendance_score AS attendance_percentage,
            g.term1,
            g.term2,
            g.term3
        FROM students s
        INNER JOIN grades g ON s.id = g.student_id
        WHERE 
            (g.attendance_score < :att_t)
            OR (g.term1 < :grade_t OR g.term2 < :grade_t OR g.term3 < :grade_t)
        ORDER BY g.attendance_score ASC
    """)

    return db.execute(query, {"att_t": attendance_threshold, "grade_t": grade_threshold}).fetchall()

def get_student_prediction_data(db: Session, student_id: int):
    query = text("""
        SELECT 
            term1, term2, term3, attendance_score
        FROM grades
        WHERE student_id = :student_id
    """)
    return db.execute(query, {"student_id": student_id}).fetchone()

def delete_student(db: Session, student_id: int):
    # This will delete the student and cascade to attendance/grades if foreign keys are set correctly
    # or we can do it manually for SQLite if needed.
    # In SQLite, PRAGMA foreign_keys = ON; must be enabled.
    db.execute(text("DELETE FROM attendance WHERE student_id = :s_id"), {"s_id": student_id})
    db.execute(text("DELETE FROM grades WHERE student_id = :s_id"), {"s_id": student_id})
    db.execute(text("DELETE FROM students WHERE id = :s_id"), {"s_id": student_id})
    db.commit()
    return True