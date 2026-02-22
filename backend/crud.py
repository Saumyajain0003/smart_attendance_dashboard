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
            ) AS attendance_percentage
        FROM students s
        JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id
        HAVING 
            (SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) * 100.0) / COUNT(a.id)
            < :threshold
    """)

    return db.execute(query, {"threshold": threshold}).fetchall()