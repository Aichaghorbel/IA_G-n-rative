from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class QCM(Base):
    __tablename__ = "qcms"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=True)
    total_questions = Column(Integer, default=5)
    score = Column(Float, nullable=True)                       # Note finale / 100
    completed = Column(Boolean, default=False)
    result_summary = Column(JSON, default=dict)                # {acquis: [], difficultes: [], motivations: ""}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("CandidateProfile", back_populates="qcms")
    formation = relationship("Formation")
    questions = relationship("Question", back_populates="qcm", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    qcm_id = Column(Integer, ForeignKey("qcms.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)                     # ["Option A", "Option B", "Option C", "Option D"]
    correct_option = Column(Integer, nullable=False)           # Index 0, 1, 2, 3
    difficulty = Column(String(20), default="moyen")           # facile, moyen, difficile
    category = Column(String(50), default="technique")         # logique, technique, motivation

    qcm = relationship("QCM", back_populates="questions")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    qcm_id = Column(Integer, ForeignKey("qcms.id"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
