"""
Module de modélisation du sous-système d'évaluation et de préinscription (QCM & Préinscriptions).
Strictement conforme au diagramme de classes UML (SmartCampus.drawio / SmartCampus-ClassDiagram.jpg).

Principes appliqués :
- SOLID (Single Responsibility, Open/Closed, Dependency Inversion)
- Clean Code & Design Patterns (DDD Aggregate, Value Object, Data Mapper)
- Strict respect des relations UML :
    * Preinscription (1) -> (1) QCM (clé étrangère `preinscription_id` sur `qcms`)
    * QCM (1) -> (1..*) Question (clé étrangère `qcm_id` sur `questions`)
    * Question (1) -> (1..*) ReponseQuestion (clé étrangère `question_id` sur `reponses_question`)
    * NOTE CRUCIALE : ReponseQuestion est liée UNIQUEMENT à Question, AUCUNE liaison directe avec QCM.
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Preinscription(Base):
    """
    Classe Preinscription (Diagramme de classes UML) :
    --------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - dateCreation : Date (Date de soumission du dossier)
    - statut : StatutPreinscription ('accepté', 'refusé')

    Associations :
    - Candidat (1) -> Preinscription (0..*) : Clé étrangère `candidat_id`
    - Formation (1) -> Preinscription (0..*) : Clé étrangère `formation_id`
    - Preinscription (1) générer (1) QCM : Relation 1-to-1 vers QCM
    """
    __tablename__ = "preinscriptions"

    id = Column(Integer, primary_key=True, index=True)
    dateCreation = Column(Date, nullable=True)
    statut = Column(String(50), nullable=False, default="accepté")  # StatutPreinscription: accepté, refusé

    # Clés étrangères vers Candidat et Formation
    candidat_id = Column(Integer, ForeignKey("candidats.id"), nullable=False, index=True)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False, index=True)

    # Relations ORM
    candidat = relationship("Candidat", back_populates="preinscriptions")
    formation = relationship("Formation", back_populates="preinscriptions")
    qcm = relationship("QCM", uselist=False, back_populates="preinscription")

    # Propriétés de compatibilité ascendante avec les contrôleurs existants
    @property
    def candidate_id(self) -> int:
        return self.candidat_id

    @property
    def date_demande(self):
        return self.dateCreation

    @property
    def decision(self):
        return self.statut

    @property
    def candidate(self):
        return self.candidat


# Alias de compatibilité
PreRegistration = Preinscription


class QCM(Base):
    """
    Classe QCM (Diagramme de classes UML) :
    --------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - score : float (Note globale obtenue)
    - datePassation : Date (Date de passage du test adaptatif)
    - niveau : NiveauQSM (Enum : 'facile', 'moyenne', 'difficile', 'Avancé', 'Intermédiaire', 'A considérer')

    Associations :
    - 1 Preinscription générer 1 QCM : Clé étrangère `preinscription_id` (1-to-1)
    - 1 QCM -> 1..* Question : Composition avec Question (cascade de suppression)
    """
    __tablename__ = "qcms"

    id = Column(Integer, primary_key=True, index=True)
    score = Column(Float, nullable=True)
    datePassation = Column(Date, nullable=True)
    niveau = Column(String(50), nullable=True)  # NiveauQSM

    # Clé étrangère exclusive vers Preinscription (généré par la préinscription)
    preinscription_id = Column(Integer, ForeignKey("preinscriptions.id"), unique=True, nullable=False, index=True)

    # Relations ORM
    preinscription = relationship("Preinscription", back_populates="qcm")
    questions = relationship("Question", back_populates="qcm", cascade="all, delete-orphan")


class Question(Base):
    """
    Classe Question (Diagramme de classes UML) :
    -------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - contenu : String (Énoncé de la question)
    - correctReponse : id (Identifiant entier de la réponse attendue)
    - niveau : NiveauQuestion (Enum: NiveauQSM)
    - categorie : Categorie (Enum: Algorithmique, logiqueMath, gestionEtEconomie)

    Associations :
    - 1 QCM -> 1..* Question : Clé étrangère `qcm_id`
    - 1 Question -> 1..* Reponse : Clé étrangère `question_id` sur la table `reponses_question`
    """
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    contenu = Column(String(1000), nullable=False)
    correctReponse = Column(Integer, nullable=True)  # id de la bonne réponse
    niveau = Column(String(50), nullable=False)      # NiveauQSM
    categorie = Column(String(50), nullable=False)   # Categorie

    # Clé étrangère reliant la question à son QCM
    qcm_id = Column(Integer, ForeignKey("qcms.id"), nullable=False, index=True)

    # Relations ORM
    qcm = relationship("QCM", back_populates="questions")
    reponses = relationship("ReponseQuestion", back_populates="question", cascade="all, delete-orphan")


class ReponseQuestion(Base):
    """
    Classe Reponse de la Question QCM (Diagramme de classes UML) :
    --------------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - estSélectionné : bool (Indique si le candidat a coché cette option)

    Association :
    - 1 Question -> 1..* Reponse : Clé étrangère `question_id` UNIQUEMENT.
      (Aucune clé étrangère vers QCM ou Candidat, conformément au diagramme officiel).
    """
    __tablename__ = "reponses_question"

    id = Column(Integer, primary_key=True, index=True)
    estSelectionne = Column("estSélectionné", Boolean, nullable=False, default=False)

    # Clé étrangère exclusive vers Question
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)

    # Relation ORM vers Question
    question = relationship("Question", back_populates="reponses")


# Alias pour la compatibilité avec le code existant
ReponseQCM = ReponseQuestion
Answer = ReponseQuestion
