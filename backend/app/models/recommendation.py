from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Formation(Base):
    __tablename__ = "formations"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    nom = Column(String(200), nullable=False)
    etablissement = Column(String(20), nullable=False)         # IIT, ISB
    cycle = Column(String(50), nullable=False)                 # Licence, Prépa, Ingénieur, Master
    duree_annees = Column(Integer, default=3)
    description = Column(Text, nullable=False)
    avantages = Column(JSON, default=list)                     # Liste des points forts
    prerequis = Column(JSON, default=list)                     # Conditions d'admission
    debouches = Column(JSON, default=list)                     # Métiers visés
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False)
    score_compatibilite = Column(Float, nullable=False)        # 0.0 à 1.0
    justification = Column(Text, nullable=False)
    status = Column(String(30), default="genere", nullable=False) # genere, valide, ajuste, refuse
    genere_par = Column(String(30), default="agent_ia")        # systeme, agent_ia
    valide_par = Column(Integer, ForeignKey("users.id"), nullable=True)
    motif_rejet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    candidate = relationship("CandidateProfile", back_populates="recommendations")
    formation = relationship("Formation")
