from pydantic import BaseModel

class AttendanceRisk(BaseModel):
    student_id: int
    name: str
    student_code: str
    total_classes: int
    present_count: int
    attendance_percentage: float