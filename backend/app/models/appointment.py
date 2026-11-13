from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    candidat_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False, index=True)
    enseignant_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    preinscription_id = Column(Integer, ForeignKey("preregistrations.id"), nullable=True)
    date_proposee = Column(DateTime, nullable=True)
    date_confirmee = Column(DateTime, nullable=True)
    status = Column(String(30), default="propose", nullable=False)  # propose, confirme, annule, termine
    lieu = Column(String(100), default="en ligne")                 # en ligne, campus IIT, campus ISB
    observations = Column(Text, nullable=True)                     # observations de l'entretien (max 2000)
    decision_finale = Column(String(30), default="en_attente")     # admis, refuse, en_attente, complement_demande
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    candidate = relationship("CandidateProfile", back_populates="appointments")
    enseignant = relationship("User", foreign_keys=[enseignant_id])


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), default="systeme")                   # confirmation, relance, rdv, systeme
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
