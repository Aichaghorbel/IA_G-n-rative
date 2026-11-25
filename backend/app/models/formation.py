"""
Module de modélisation de l'offre académique (Formations, Tarifs, Équivalences, Spécialités, Programmes, Matières).
Strictement conforme au diagramme de classes UML (SmartCampus.drawio / SmartCampus-ClassDiagram.jpg).

Principes appliqués :
- SOLID :
    * SRP : Chaque classe gère son niveau d'abstraction académique (Formation -> Spécialité -> Programme -> Matière).
    * OCP : Possibilité d'ajouter des programmes, semestres et matières sans impacter la classe Formation.
- Clean Code & Design Patterns :
    * Composite Pattern (Hiérarchie Formation -> Specialite -> ProgrammeEtude -> Matiere).
    * Many-to-Many Association Table (`formation_candidat`).
"""

from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.core.database import Base

# ==============================================================================
# Table d'association UML : Candidat (0..*) s'inscrire (0..*) Formation
# ==============================================================================
Formation_Candidat_association = Table(
    "formation_candidat",
    Base.metadata,
    Column("formation_id", Integer, ForeignKey("formations.id"), primary_key=True),
    Column("candidat_id", Integer, ForeignKey("candidats.id"), primary_key=True)
)


class Formation(Base):
    """
    Classe Formation conforme au diagramme de classes UML :
    -------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - nom : String (Intitulé officiel de la formation)
    - universite : Universite (Enum: 'IIT', 'ISB')
    - description : String
    - objectif : String
    - duree : int (Durée en années, ex: 3 pour Licence, 5 pour Ingénieur)
    - debouches : String (Perspectives professionnelles)
    - conditionsAdmission : String
    - prerequis : String

    Associations :
    - 1 Formation posséder 1..* Tarif
    - 1 Formation concerner 0..* Equivalence
    - 1 Formation -> 1..* Specialite
    - 0..* Formation s'inscrire 0..* Candidat (via `formation_candidat`)
    - 1 Formation -> Preinscription (0..*)
    NOTE : Pas de liaison directe avec Recommandation dans le diagramme.
    """
    __tablename__ = "formations"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(200), nullable=False)
    universite = Column(String(50), nullable=False)  # Universite enum: IIT, ISB
    description = Column(String(1000), nullable=False)
    objectif = Column(String(1000), nullable=True)
    duree = Column(Integer, default=3)
    debouches = Column(String(1000), nullable=True)
    conditionsAdmission = Column(String(1000), nullable=True)
    prerequis = Column(String(1000), nullable=True)

    # Statut de publication et période de validité (Gouvernance & Validité)
    statut_publication = Column(String(50), default="publie", nullable=False)
    date_debut_validite = Column(Date, nullable=True)
    date_fin_validite = Column(Date, nullable=True)

    # 1 Formation posséder 1..* Tarif
    tarifs = relationship("Tarif", back_populates="formation", cascade="all, delete-orphan")

    # 1 Formation concerner 0..* Equivalence
    equivalences = relationship("Equivalence", back_populates="formation", cascade="all, delete-orphan")

    # 1 Formation -> 1..* Specialite
    specialites = relationship("Specialite", back_populates="formation", cascade="all, delete-orphan")

    # 0..* Formation s'inscrire 0..* Candidat
    candidats = relationship("Candidat", secondary=Formation_Candidat_association, back_populates="formations")

    # 1 Formation -> Preinscription
    preinscriptions = relationship("Preinscription", back_populates="formation")
    # NOTE : recommandations supprimé — absent du diagramme de classes


class Tarif(Base):
    """
    Classe Tarif conforme au diagramme de classes UML :
    ---------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - montant/9mois : float (Frais de scolarité sur 9 mois)
    - type : TypeTarif (Enum: 'fraisNational', 'frais international')
    - Annee : String (Année universitaire, ex: '2026-2027')
    - devise : Devise (Enum: 'DT', '€')

    Association :
    - 1 Formation posséder 1..* Tarif (clé étrangère `formation_id`)
    """
    __tablename__ = "tarifs"

    id = Column(Integer, primary_key=True, index=True)
    montant_9mois = Column("montant/9mois", Float, nullable=False)
    type = Column(String(50), nullable=False)         # TypeTarif: fraisNational, frais international
    Annee = Column("Annee", String(50), nullable=False)
    devise = Column(String(10), nullable=False)        # Devise: DT, €
    modalites_paiement = Column(String(500), nullable=True)

    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False, index=True)

    @property
    def annee(self) -> str:
        return self.Annee

    @annee.setter
    def annee(self, val: str):
        self.Annee = val

    # 1 Formation posséder 1..* Tarif
    formation = relationship("Formation", back_populates="tarifs")


class Equivalence(Base):
    """
    Classe Equivalence conforme au diagramme de classes UML :
    ---------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - desciption : String (Description des passerelles et équivalences)
    - conditions : String
    - formation_Origine : Diplome (Enum: Baccalauréat, Prépa, Licence, Mastère)

    Association :
    - 1 Formation concerner 0..* Equivalence (clé étrangère `formation_id`)
    """
    __tablename__ = "equivalences"

    id = Column(Integer, primary_key=True, index=True)
    desciption = Column(String(1000), nullable=True)
    conditions = Column(String(1000), nullable=True)
    formation_Origine = Column(String(50), nullable=False)  # Diplome enum

    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False, index=True)

    # 1 Formation concerner 0..* Equivalence
    formation = relationship("Formation", back_populates="equivalences")


class Specialite(Base):
    """
    Classe Specialite conforme au diagramme de classes UML :
    --------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - nom : String (Intitulé de la spécialité, ex: 'Génie Logiciel & Cloud')
    - description : String

    Associations :
    - 1 Formation -> 1..* Specialite (clé étrangère `formation_id`)
    - 1 Specialite -> 1..* ProgrammeEtude
    """
    __tablename__ = "specialites"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=True)

    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False, index=True)

    # Relations ORM
    formation = relationship("Formation", back_populates="specialites")
    programmes = relationship("ProgrammeEtude", back_populates="specialite", cascade="all, delete-orphan")


class ProgrammeEtude(Base):
    """
    Classe ProgrammeEtude conforme au diagramme de classes UML :
    ------------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - nom : String (Intitulé du programme d'étude)
    - description : String
    - semestre : int (Numéro de semestre d'études : 1, 2, ...)

    Associations :
    - 1 Specialite -> 1..* ProgrammeEtude (clé étrangère `specialite_id`)
    - 1 ProgrammeEtude -> 1..* Matiere
    """
    __tablename__ = "programmes_etude"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=True)
    semestre = Column(Integer, nullable=False, default=1)

    specialite_id = Column(Integer, ForeignKey("specialites.id"), nullable=False, index=True)

    # Relations ORM
    specialite = relationship("Specialite", back_populates="programmes")
    matieres = relationship("Matiere", back_populates="programme", cascade="all, delete-orphan")


class Matiere(Base):
    """
    Classe Matiere conforme au diagramme de classes UML :
    -----------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - nom : String (Nom du module / matière enseignée)
    - description : String
    - coefficient : int (Coefficient de pondération)
    - volumeHoraire : int (Nombre total d'heures d'enseignement)

    Association :
    - 1 ProgrammeEtude -> 1..* Matiere (clé étrangère `programme_id`)
    """
    __tablename__ = "matieres"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=True)
    coefficient = Column(Integer, nullable=False, default=1)
    volumeHoraire = Column(Integer, nullable=False, default=42)

    programme_id = Column(Integer, ForeignKey("programmes_etude.id"), nullable=False, index=True)

    # Relation ORM
    programme = relationship("ProgrammeEtude", back_populates="matieres")
