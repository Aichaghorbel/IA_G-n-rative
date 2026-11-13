from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)  # Associé à la session visiteur (V)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    telephone = Column(String(30), nullable=True)
    
    niveau_etudes = Column(String(50), nullable=True, default="bac")  # lycéen, bac, bac+1, bac+2, bac+3, équivalence
    etablissement_origine = Column(String(200), nullable=True)
    specialites = Column(JSON, default=list)        # max 5 éléments
    interets = Column(JSON, default=list)           # max 10 éléments
    matieres_preferees = Column(JSON, default=list) # max 5
    objectif_professionnel = Column(Text, nullable=True)
    contraintes = Column(Text, nullable=True)
    etablissement_vise = Column(String(20), default="indifférent")  # IIT, ISB, indifférent

    # Machine à états stricte (Section 3.2 et 4.4.1)
    # EXPLORATION -> PROFIL_ENRICHI -> PREINSCRIT -> QCM_FAIT -> ENTRETIEN_PLANIFIE -> ENTRETIEN_REALISE -> INSCRIT | ABANDONNE
    statut_dossier = Column(String(50), default="EXPLORATION", nullable=False)

    enseignant_affecte_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    affectation_statut = Column(String(30), nullable=True)  # auto_proposed, valide, refuse
    motif_affectation = Column(Text, nullable=True)
    
    consent_rgpd = Column(Boolean, default=False, nullable=False)
    consent_timestamp = Column(DateTime, nullable=True)
    consent_ip = Column(String(45), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", foreign_keys=[user_id])
    enseignant_affecte = relationship("User", foreign_keys=[enseignant_affecte_id])
    preregistrations = relationship("PreRegistration", back_populates="candidate")
    recommendations = relationship("Recommendation", back_populates="candidate")
    qcms = relationship("QCM", back_populates="candidate")
    appointments = relationship("Appointment", back_populates="candidate")


class PreRegistration(Base):
    __tablename__ = "preregistrations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=True)
    date_demande = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    decision = Column(String(50), default="en_attente")  # en_attente, acceptee, refusee, ajustee
    observations = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    candidate = relationship("CandidateProfile", back_populates="preregistrations")
    formation = relationship("Formation")
