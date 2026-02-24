import csv
import io
import os
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.database import SessionLocal, init_db
from backend import schemas, crud
from backend.models.predictor import StudentPredictor

app = FastAPI(title="Smart Attendance System")

@app.on_event("startup")
def startup_event():
    init_db()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "online", "message": "Smart Attendance API is running"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get(
    "/attendance/at-risk",
    response_model=list[schemas.AttendanceRisk]
)
def students_at_risk(
    attendance_threshold: int = 75,
    grade_threshold: int = 50,
    db: Session = Depends(get_db)
):
    rows = crud.get_students_at_risk(db, attendance_threshold, grade_threshold)
    return [dict(row._mapping) for row in rows]

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.execute(text("SELECT COUNT(*) FROM students")).fetchone()[0]
    avg_att_res = db.execute(text("SELECT AVG(attendance_score) FROM grades")).fetchone()[0]
    avg_att = float(avg_att_res) if avg_att_res is not None else 0.0
    return {
        "total_students": total,
        "avg_attendance": round(avg_att, 1)
    }

@app.get("/students")
def get_all_students(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            s.id AS student_id, s.name, s.student_code,
            g.attendance_score AS attendance_percentage,
            g.term1, g.term2, g.term3
        FROM students s
        LEFT JOIN grades g ON s.id = g.student_id
        ORDER BY s.name ASC
    """)
    result = db.execute(query)
    # Convert to list of dicts for proper serialization
    return [dict(row._mapping) for row in result]

@app.post("/students/upload-csv")
def upload_students_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Expected CSV: name,email,student_code,term1,term2,term3,attendance_score
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    
    try:
        count = 0
        for row in reader:
            # 1. UPSERT Student (Check both code and email for identification)
            # Find if student already exists by code OR email
            existing = db.execute(text("""
                SELECT id FROM students WHERE student_code = :code OR email = :email
            """), {"code": row['student_code'], "email": row['email']}).fetchone()
            
            if existing:
                s_id = existing[0]
                # Update existing record
                db.execute(text("""
                    UPDATE students 
                    SET name = :name, email = :email, student_code = :code
                    WHERE id = :s_id
                """), {"name": row['name'], "email": row['email'], "code": row['student_code'], "s_id": s_id})
            else:
                # Insert new record
                s_id = db.execute(text("""
                    INSERT INTO students (name, email, student_code) 
                    VALUES (:name, :email, :code) 
                    RETURNING id
                """), {"name": row['name'], "email": row['email'], "code": row['student_code']}).fetchone()[0]
            
            # 2. UPSERT Grade
            db.execute(text("""
                INSERT INTO grades (student_id, course_id, term1, term2, term3, attendance_score, final_passed)
                VALUES (:s_id, 1, :t1, :t2, :t3, :att, 0)
                ON CONFLICT(student_id, course_id) DO UPDATE SET 
                    term1=excluded.term1, term2=excluded.term2, term3=excluded.term3, attendance_score=excluded.attendance_score
            """), {
                "s_id": s_id, 
                "t1": float(row['term1']), "t2": float(row['term2']), "t3": float(row['term3']),
                "att": float(row['attendance_score'])
            })
            count += 1
        
        db.commit()
        return {"status": "success", "message": f"Successfully imported {count} students."}
    except Exception as e:
        db.rollback()
        print(f"❌ Upload Error: {str(e)}")
        return {"status": "error", "message": f"Failed to process CSV: {str(e)}"}

predictor = StudentPredictor()

@app.get("/predict/success/{student_id}", response_model=schemas.SuccessPrediction)
def predict_student_success(student_id: int, db: Session = Depends(get_db)):
    data = crud.get_student_prediction_data(db, student_id)
    if not data:
        return {
            "student_id": student_id,
            "predicted_pass": False,
            "probability": 0.0,
            "model_used": "None",
            "message": "Student data not found in grades table."
        }
    
    # Extract data
    t1, t2, t3, att = data
    
    # Run prediction
    prediction, probability = predictor.predict(t1, t2, t3, att)
    
    # Get model info
    model_info_path = os.path.join(os.path.dirname(__file__), "models", "model_info.txt")
    model_name = "Unknown"
    if os.path.exists(model_info_path):
        with open(model_info_path, "r") as f:
            model_name = f.readline().split(": ")[1].strip()

    return {
        "student_id": student_id,
        "predicted_pass": bool(prediction),
        "probability": round(float(probability), 2),
        "model_used": model_name,
        "message": "Prediction successful based on Term marks and Attendance."
    }

@app.post("/predict/realtime", response_model=schemas.SuccessPrediction)
def predict_realtime_success(input_data: schemas.RealTimePredictionInput):
    # Run prediction directly from input
    prediction, probability = predictor.predict(
        input_data.term1, 
        input_data.term2, 
        input_data.term3, 
        input_data.attendance_score
    )
    
    # Get model info
    model_info_path = os.path.join(os.path.dirname(__file__), "models", "model_info.txt")
    model_name = "Unknown"
    if os.path.exists(model_info_path):
        with open(model_info_path, "r") as f:
            model_name = f.readline().split(": ")[1].strip()

    return {
        "student_id": None, # Non-DB students don't have an ID
        "predicted_pass": bool(prediction),
        "probability": round(float(probability), 2),
        "model_used": model_name,
        "message": f"Real-time prediction for {input_data.name} successful."
    }

@app.delete("/students/{student_id}")
def remove_failed_student(student_id: int, db: Session = Depends(get_db)):
    # Check if student exists and failed (optional logic)
    # For now, just delete as requested
    success = crud.delete_student(db, student_id)
    if success:
        return {"status": "success", "message": f"Student {student_id} removed from system."}
    return {"status": "error", "message": "Could not delete student."}