"""
Module de modélisation du moteur de Recommandation d'orientation académique.
Strictement conforme au diagramme de classes UML (SmartCampus.drawio / SmartCampus-ClassDiagram.jpg).

Principes appliqués :
- SOLID :
    * SRP : Encapsule l'attribution de recommandations personnalisées aux candidats.
- Clean Code & Design Patterns :
    * Association binaire simple vers Candidat uniquement.
    * Value Object / Scoring Model.
NOTE : Pas de liaison directe avec Formation dans le diagramme de classes.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recommandation(Base):
    """
    Classe Recommandation conforme au diagramme de classes UML :
    ------------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - nom : String (Intitulé de la recommandation)
    - scoreComptabilite : float (Score d'affinité / compatibilité calculé entre 0.0 et 1.0 ou pourcentage)
    - justification : String (Explication argumentée fournie par l'agent IA)
    - dateGeneration : DateTime (Date et heure de génération de la recommandation)
    - statut : StatutRecommandation (Enum: 'validée', 'ajustée', 'à validée')

    Associations (strictement selon le diagramme) :
    - Candidat (1) recevoir (0..*) Recommandation (clé `candidat_id`)
    NOTE : formation_id supprimé — Recommandation n'est liée qu'au Candidat dans le diagramme.
    """
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=True)
    scoreComptabilite = Column(Float, nullable=False, default=0.0)
    justification = Column(String(2000), nullable=False)
    dateGeneration = Column(DateTime, nullable=True)
    statut = Column(String(50), nullable=False, default="à validée")  # StatutRecommandation: validée, ajustée, à validée

    # FK : Candidat recevoir Recommandation
    candidat_id = Column(Integer, ForeignKey("candidats.id"), nullable=False, index=True)
    # NOTE : formation_id supprimé — absent du diagramme de classes

    # Relation ORM
    candidat = relationship("Candidat", back_populates="recommandations")

    @property
    def candidate_id(self) -> int:
        return self.candidat_id

    @property
    def score_compatibilite(self) -> float:
        return self.scoreComptabilite

    @property
    def status(self) -> str:
        return self.statut

    @property
    def created_at(self):
        return self.dateGeneration

    @property
    def candidate(self):
        return self.candidat


# Alias de compatibilité
Recommendation = Recommandation
