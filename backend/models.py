from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    roll_number = Column(String, unique=True)
    class_name = Column(String)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    performances = relationship("Performance", back_populates="student")
    feedbacks = relationship("Feedback", back_populates="student")


class Performance(Base):
    __tablename__ = "performance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    subject = Column(String)
    marks = Column(Float)
    exam_type = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="performances")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    feedback = Column(String)
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="feedbacks")


