from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend import schemas, crud

app = FastAPI(title="Smart Attendance System")

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
    "/attendance/below-threshold",
    response_model=list[schemas.AttendanceRisk]
)
def students_below_threshold(
    threshold: int = 75,
    db: Session = Depends(get_db)
):
    rows = crud.get_students_below_threshold(db, threshold)
    return rows

from backend.models.predictor import StudentPredictor
import os

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
        "probability": round(probability, 2),
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
        "probability": round(probability, 2),
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