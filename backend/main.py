from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend import schemas, crud

app = FastAPI(title="Smart Attendance System")

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