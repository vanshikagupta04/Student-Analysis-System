from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
import json

from .database import engine
from . import models
from .auth import get_db, authenticate_user, create_access_token, get_current_user
from .schemas import StudentCreate, StudentResponse, PerformanceCreate, PerformanceResponse, FeedbackCreate, FeedbackResponse, PredictRequest
from datetime import datetime
import joblib

model = joblib.load("backend/model.pkl")
subject_encoder = joblib.load("backend/subject_encoder.pkl")
exam_encoder = joblib.load("backend/exam_encoder.pkl")


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Student Analytics System Running"}

# 🔐 login
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/protected")
def protected(user = Depends(get_current_user)):
    return {"message": f"Welcome {user.username}"}

@app.post("/students", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    new_student = models.Student(**student.dict())
    db.add(new_student)
    db.commit()
    db.refresh(new_student)
    return new_student

@app.get("/students", response_model=list[StudentResponse])
def get_students(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Student).all()


@app.get("/students/search", response_model=list[StudentResponse])
def search_students(name: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Student).filter(models.Student.name.contains(name)).all()


@app.post("/performance", response_model=PerformanceResponse)
def add_performance(perf: PerformanceCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    new_perf = models.Performance(**perf.dict())
    db.add(new_perf)
    db.commit()
    db.refresh(new_perf)
    return new_perf


@app.get("/performance", response_model=list[PerformanceResponse])
def get_performance(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Performance).all()


@app.post("/feedback", response_model=FeedbackResponse)
def create_feedback(
    fb: FeedbackCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    new_fb = models.Feedback(**fb.dict())
    db.add(new_fb)
    db.commit()
    db.refresh(new_fb)
    return new_fb

@app.get("/feedback", response_model=list[FeedbackResponse])
def get_feedback(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return db.query(models.Feedback).all()

@app.get("/students/filter", response_model=list[StudentResponse])
def filter_students(
    name: str = None,
    class_name: str = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    query = db.query(models.Student)

    if name:
        query = query.filter(models.Student.name.contains(name))
    if class_name:
        query = query.filter(models.Student.class_name == class_name)

    return query.all()


@app.get("/performance/filter", response_model=list[PerformanceResponse])
def filter_performance(
    subject: str = None,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    query = db.query(models.Performance)

    if subject:
        query = query.filter(models.Performance.subject == subject)

    if start_date and end_date:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        query = query.filter(models.Performance.date.between(start, end))

    return query.all()

@app.get("/analytics/average-marks")
def average_marks(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    results = (
        db.query(
            models.Performance.subject,
            func.avg(models.Performance.marks).label("average_marks")
        )
        .group_by(models.Performance.subject)
        .all()
    )

    return [{"subject": r[0], "average_marks": round(r[1], 2)} for r in results]

@app.get("/analytics/top-students")
def top_students(
    limit: int = 5,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    results = (
        db.query(
            models.Student.name,
            func.sum(models.Performance.marks).label("total_marks")
        )
        .join(models.Performance)
        .group_by(models.Student.id)
        .order_by(func.sum(models.Performance.marks).desc())
        .limit(limit)
        .all()
    )

    return [{"name": r[0], "total_marks": r[1]} for r in results]


@app.get("/analytics/class-performance")
def class_performance(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    results = (
        db.query(
            models.Student.class_name,
            func.avg(models.Performance.marks).label("avg_marks")
        )
        .join(models.Performance)
        .group_by(models.Student.class_name)
        .all()
    )

    return [{"class": r[0], "average_marks": round(r[1], 2)} for r in results]


@app.get("/analytics/marks-distribution")
def marks_distribution(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    results = db.query(models.Performance.marks).all()

    return [r[0] for r in results]


@app.get("/meta/subjects")
def get_subjects(user=Depends(get_current_user)):
    return subject_encoder.classes_.tolist()

@app.get("/meta/exam-types")
def get_exam_types(user=Depends(get_current_user)):
    return exam_encoder.classes_.tolist()


@app.post("/predict")
def predict(req: PredictRequest, user=Depends(get_current_user)):
    try:
        subject_enc = subject_encoder.transform([req.subject])[0]
        exam_enc = exam_encoder.transform([req.exam_type])[0]
    except ValueError:
        return {
            "error": "Unknown subject or exam_type. Use values seen during training."
        }

    X = [[req.marks, subject_enc, exam_enc]]

    pred = model.predict(X)[0]

    proba_array = model.predict_proba(X)[0]

    # 🔐 Safe handling for single-class model
    if len(proba_array) == 1:
        proba = float(proba_array[0])
    else:
        proba = float(proba_array[1])

    return {
        "prediction": "Pass" if pred == 1 else "Fail",
        "probability": round(proba, 3)
    }

    return {
        "prediction": "Pass" if pred == 1 else "Fail",
        "probability": round(float(proba), 3)
    }

@app.get("/model/metrics")
def get_metrics(user=Depends(get_current_user)):
    with open("backend/model_metrics.json") as f:
        return json.load(f)