"""
Module de modélisation des Rendez-vous, Entretiens d'orientation et Notifications.
Strictement conforme au diagramme de classes UML (SmartCampus.drawio / SmartCampus-ClassDiagram.jpg).

Principes appliqués :
- SOLID :
    * SRP : RendezVous (gestion de créneau & canal), Entretien (évaluation pédagogique), Notification (alerte utilisateur).
    * DIP : Abstraction ORM via SQLAlchemy.
- Clean Code & Design Patterns :
    * Observer / Notification Pattern pour les notifications émises aux utilisateurs.
    * 1-to-1 Association (RendezVous -> 0..1 Entretien).
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class RendezVous(Base):
    """
    Classe RendezVous conforme au diagramme de classes UML :
    ---------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - dateHeure : DateTime (Horodatage du rendez-vous)
    - statut : StatutRDV (Enum: 'confirmé', 'reporté', 'Annulé')
    - salleOuLien : String (Salle physique sur le campus ou URL visio)

    Associations (strictement selon le diagramme) :
    - Enseignant organiser 0..* RendezVous (clé `enseignant_id`)
    - Candidat agir 0..* RendezVous (clé `candidat_id`)
    - 1 RendezVous mener 0..1 Entretien
    NOTE : responsable_id supprimé — absent du diagramme de classes.
    """
    __tablename__ = "rendezvous"

    id = Column(Integer, primary_key=True, index=True)
    dateHeure = Column(DateTime, nullable=True)
    statut = Column(String(50), nullable=False, default="confirmé")  # StatutRDV
    salleOuLien = Column(String(255), nullable=True)

    # FK : Enseignant organiser RendezVous
    enseignant_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    # FK : Candidat agir RendezVous
    candidat_id = Column(Integer, ForeignKey("candidats.id"), nullable=False, index=True)
    # NOTE : responsable_id supprimé — absent du diagramme de classes

    # Relations ORM
    enseignant = relationship("Enseignant", foreign_keys=[enseignant_id], back_populates="rendezvous_organises")
    candidat = relationship("Candidat", back_populates="rendezvous")
    entretien = relationship("Entretien", uselist=False, back_populates="rendezvous", cascade="all, delete-orphan")

    @property
    def status(self) -> str:
        return self.statut

    @property
    def lieu(self) -> str:
        return self.salleOuLien or ""

    @property
    def candidate(self):
        return self.candidat


# Alias de compatibilité
Appointment = RendezVous


class Entretien(Base):
    """
    Classe Entretien conforme au diagramme de classes UML :
    -------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - avisEnseignant : Avis (Enum: 'Favorable', 'Défavorable')
    - notes : String (Commentaires et observations pédagogiques)
    - oriantationFinale : DiplomeSouhaite (Enum des filières IIT & ISB)
    - staut : SatutEntretien (Enum: 'Planifié', 'Terminé')

    Associations (strictement selon le diagramme) :
    - 1 RendezVous mener 0..1 Entretien (clé `rendezvous_id`, 1-to-1)
    NOTE : enseignant_id supprimé — l'Entretien est lié au RendezVous, pas directement à l'Enseignant.
    """
    __tablename__ = "entretiens"

    id = Column(Integer, primary_key=True, index=True)
    avisEnseignant = Column(String(50), nullable=True)      # Avis: Favorable, Défavorable
    notes = Column(String(2000), nullable=True)
    oriantationFinale = Column(String(100), nullable=True)   # DiplomeSouhaite enum
    staut = Column(String(50), nullable=False, default="Planifié")  # SatutEntretien: Planifié, Terminé

    # FK : RendezVous mener Entretien (1-to-1)
    rendezvous_id = Column(Integer, ForeignKey("rendezvous.id"), unique=True, nullable=False, index=True)
    # NOTE : enseignant_id supprimé — absent du diagramme de classes

    # Relations ORM
    rendezvous = relationship("RendezVous", back_populates="entretien")


class Notification(Base):
    """
    Classe Notification conforme au diagramme de classes UML :
    -----------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - type : typeNotif (Enum: 'Confirmation', 'Annonce')
    - contenu : String (Message textuel de notification)
    - dateEnvoi : Date / DateTime
    - envoyee : bool (Statut d'émission/lecture)

    Association :
    - 1 Utilisateur recevoir 0..* Notification (clé `user_id`)
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, default="Confirmation")  # TypeNotif: Confirmation, Annonce
    contenu = Column(String(1000), nullable=False)
    dateEnvoi = Column(DateTime, nullable=True)
    envoyee = Column(Boolean, nullable=False, default=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relation ORM
    utilisateur = relationship("User", back_populates="notifications")

    @property
    def title(self) -> str:
        return self.type

    @property
    def message(self) -> str:
        return self.contenu

    @property
    def is_read(self) -> bool:
        return not self.envoyee

    @is_read.setter
    def is_read(self, val: bool) -> None:
        self.envoyee = not bool(val)

    @property
    def created_at(self) -> datetime:
        return self.dateEnvoi or datetime.now(timezone.utc).replace(tzinfo=None)
