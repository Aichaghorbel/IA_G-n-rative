"""
Module de modélisation des entités Visiteur, Candidat et ProfilCandidat.
Strictement conforme au diagramme de classes UML (SmartCampus.drawio / SmartCampus-ClassDiagram.jpg).

Principes appliqués :
- SOLID :
    * SRP : Visiteur (session anonyme), Candidat (identité officielle), ProfilCandidat (dossier académique).
    * ISP : Schémas et relations distincts pour chaque étape du cycle de vie candidat.
- Clean Code & Design Patterns :
    * State/Lifecycle Pattern (Visiteur -> conversion en -> Candidat).
    * Many-to-Many Association Table (`formation_candidat`) pour `s'inscrire`.
"""

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.formation import Formation_Candidat_association


class Visiteur(Base):
    """
    Classe Visiteur conforme au diagramme de classes UML :
    -------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - sessionToken : String (Jeton anonyme persistant 30j)
    - ip_address : String (Adresse IP client)
    - dateVisite : Date (Date de première visite)

    Associations :
    - 1 Visiteur devenir 1 Candidat (clé étrangère `visiteur_id` sur la table `candidats`)
    - Visiteur démarrer 0..* Conversation
    """
    __tablename__ = "visiteurs"

    id = Column(Integer, primary_key=True, index=True)
    sessionToken = Column(String(255), unique=True, index=True, nullable=False)
    ip_address = Column(String(50), nullable=True)
    dateVisite = Column(Date, nullable=True)

    # 1 Visiteur devenir 1 Candidat
    candidat = relationship("Candidat", uselist=False, back_populates="visiteur")

    # Visiteur démarrer 0..* Conversation
    conversations = relationship("Conversation", back_populates="visiteur")


class Candidat(Base):
    """
    Classe Candidat conforme au diagramme de classes UML :
    -------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - CIN : String (Numéro de carte d'identité nationale)
    - passport : String (Numéro de passeport)
    - pays : String (Pays d'origine)
    - dateNaissance : Date (Date de naissance)
    - sexe : Sexe (Enum: 'Homme', 'Femme')
    - adresse : String (Adresse de résidence)
    - universite : Universite (Enum: 'IIT', 'ISB')

    Associations :
    - 1 Visiteur devenir 1 Candidat (visiteur_id)
    - 1 Candidat avoir 1 ProfilCandidat (profil)
    - Candidat (0..*) s'inscrire (0..*) Formation (via table d'association `formation_candidat`)
    - 1 Candidat -> Preinscription (0..*)
    - 1 Candidat recevoir 0..* Recommandation
    - Candidat démarrer 0..* Conversation
    - Candidat agir 0..* RendezVous
    """
    __tablename__ = "candidats"

    id = Column(Integer, primary_key=True, index=True)
    CIN = Column("CIN", String(50), nullable=True, index=True)
    passport = Column(String(50), nullable=True)
    pays = Column(String(100), nullable=True)
    dateNaissance = Column(Date, nullable=True)
    sexe = Column(String(20), nullable=True)          # Sexe enum: Homme, Femme
    adresse = Column(String(255), nullable=True)
    universite = Column(String(50), nullable=True)    # Universite enum: IIT, ISB

    # Clé étrangère 1 Visiteur devenir 1 Candidat
    visiteur_id = Column(Integer, ForeignKey("visiteurs.id"), unique=True, nullable=True, index=True)

    # Clé étrangère optionnelle vers le compte User pour l'authentification
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True, index=True)

    # Propriétés de compatibilité ascendante
    @property
    def email(self) -> str:
        if self.user:
            return self.user.email
        return ""

    @property
    def nom(self) -> str:
        if self.user:
            return self.user.nom
        return ""

    @property
    def prenom(self) -> str:
        if self.user:
            return self.user.prenom
        return ""

    @property
    def candidate_id(self) -> int:
        return self.id

    # Relations ORM
    visiteur = relationship("Visiteur", back_populates="candidat")
    user = relationship("User", foreign_keys=[user_id])
    profil = relationship("ProfilCandidat", uselist=False, back_populates="candidat", cascade="all, delete-orphan")
    formations = relationship("Formation", secondary=Formation_Candidat_association, back_populates="candidats")
    preinscriptions = relationship("Preinscription", back_populates="candidat", cascade="all, delete-orphan")
    recommandations = relationship("Recommandation", back_populates="candidat", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="candidat")
    rendezvous = relationship("RendezVous", back_populates="candidat")

    # Alias de compatibilité
    @property
    def preregistrations(self):
        return self.preinscriptions


class ProfilCandidat(Base):
    """
    Classe ProfilCandidat conforme au diagramme de classes UML :
    ------------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - dernierDiplomeObtenu : Diplome (Enum: Baccalauréat, Prépa, Licence, Mastère)
    - annéeObtention : String (Année d'obtention du diplôme précédent)
    - diplomeSouhaite : DiplomeSouhaite (Enum des 27 cursus IIT & ISB)
    - niveau : Niveau (Enum: 1, 2, 3)
    - cours : Cours (Enum: 'cours de jour', 'cours de soir')
    - sourceConnaissanceUniversité : Source (Enum: 'Réseaux sociaux', 'Amis/Parents', 'Site Web', etc.)

    Association :
    - 1 Candidat avoir 1 ProfilCandidat (clé étrangère `candidat_id`)
    """
    __tablename__ = "profils_candidat"

    id = Column(Integer, primary_key=True, index=True)
    candidat_id = Column(Integer, ForeignKey("candidats.id"), unique=True, nullable=False, index=True)

    dernierDiplomeObtenu = Column(String(50), nullable=True)          # Diplome enum
    anneeObtention = Column("annéeObtention", String(20), nullable=True)
    diplomeSouhaite = Column(String(100), nullable=True)              # DiplomeSouhaite enum
    niveau = Column(Integer, nullable=True)                           # Niveau enum (1, 2, 3)
    cours = Column(String(50), nullable=True)                         # Cours enum: cours de jour, cours de soir
    sourceConnaissanceUniversite = Column("sourceConnaissanceUniversité", String(50), nullable=True)  # Source enum

    # 1 Candidat avoir 1 ProfilCandidat
    candidat = relationship("Candidat", back_populates="profil")


# Alias de compatibilité
CandidateProfile = Candidat

# Import et réexport pour la compatibilité avec les imports historiques
from app.models.qcm import Preinscription, PreRegistration
