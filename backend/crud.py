from sqlalchemy.orm import Session
from sqlalchemy import text

def get_students_below_threshold(db: Session, threshold: int):
    query = text("""
        SELECT 
            s.id AS student_id,
            s.name,
            s.student_code,
            COUNT(a.id) AS total_classes,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
            ROUND(
                (SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0) / COUNT(a.id),
                2
            ) AS attendance_percentage,
            g.term1,
            g.term2,
            g.term3
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        LEFT JOIN grades g ON s.id = g.student_id
        GROUP BY s.id
        HAVING 
            (SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0) / COUNT(a.id)
            < :threshold
    """)

    return db.execute(query, {"threshold": threshold}).fetchall()

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