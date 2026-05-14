from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str


# 👤 Student
class StudentCreate(BaseModel):
    name: str
    roll_number: str
    class_name: str
    email: str

class StudentResponse(BaseModel):
    id: int
    name: str
    roll_number: str
    class_name: str
    email: str

    class Config:
        from_attributes = True


# 📊 Performance
class PerformanceCreate(BaseModel):
    student_id: int
    subject: str
    marks: float
    exam_type: str

class PerformanceResponse(BaseModel):
    id: int
    student_id: int
    subject: str
    marks: float
    exam_type: str

    class Config:
        from_attributes = True

# 💬 Feedback
class FeedbackCreate(BaseModel):
    student_id: int
    feedback: str
    rating: int

class FeedbackResponse(BaseModel):
    id: int
    student_id: int
    feedback: str
    rating: int

    class Config:
        from_attributes = True

class PredictRequest(BaseModel):
    marks: float
    subject: str
    exam_type: str