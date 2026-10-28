import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # student, admin, enseignant
    avatar = Column(String(500), nullable=True)
    university = Column(String(255), nullable=True)
    field = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student_details = relationship("StudentDetail", back_populates="user", uselist=False, cascade="all, delete-orphan")
    courses = relationship("Course", back_populates="teacher")
    activities = relationship("Activity", back_populates="user", cascade="all, delete-orphan")

class StudentDetail(Base):
    __tablename__ = "student_details"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    cin_passport = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    birth_date = Column(String(50), nullable=True)
    sex = Column(String(20), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    last_diploma = Column(String(100), nullable=True)
    diploma_year = Column(String(20), nullable=True)
    desired_diploma = Column(String(255), nullable=True)
    level = Column(String(50), nullable=True)
    course_time = Column(String(50), nullable=True)
    known_by = Column(String(100), nullable=True)

    user = relationship("User", back_populates="student_details")

class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    students_count = Column(Integer, default=0)
    schedule = Column(String(100), nullable=False)
    room = Column(String(100), nullable=False)

    teacher = relationship("User", back_populates="courses")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(255), nullable=False)
    type = Column(String(50), default="chat")  # chat, email, doc, profile
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activities")

class FAQQuestion(Base):
    __tablename__ = "faq_questions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(String(255), nullable=False)
    count = Column(Integer, default=0)
    category = Column(String(100), nullable=False)

