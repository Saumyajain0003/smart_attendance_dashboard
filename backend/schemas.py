from pydantic import BaseModel
from typing import Optional
class AttendanceRisk(BaseModel):
    student_id: int
    name: str
    student_code: str
    total_classes: int
    present_count: int
    attendance_percentage: float
    term1: Optional[float] = 0.0
    term2: Optional[float] = 0.0
    term3: Optional[float] = 0.0

class SuccessPrediction(BaseModel):
    student_id: Optional[int] = None
    predicted_pass: bool
    probability: float
    model_used: str
    message: str

class RealTimePredictionInput(BaseModel):
    name: str
    term1: float
    term2: float
    term3: float
    attendance_score: float