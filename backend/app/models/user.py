"""
Module de modélisation des Utilisateurs et de la hiérarchie des acteurs du système.
Strictement conforme au diagramme de classes UML (SmartCampus.drawio / SmartCampus-ClassDiagram.jpg).

Principes appliqués :
- SOLID :
    * SRP : Chaque classe gère son propre rôle et périmètre métier.
    * OCP : Extensibilité par sous-typage polymorphique SQLAlchemy (Single Table Inheritance).
    * LSP : Enseignant et Responsable peuvent se substituer à Utilisateur partout où User est requis.
- Clean Code & Design Patterns :
    * Single Table Inheritance (STI) pour centraliser l'authentification et les accès dans la table `users`.
    * Data Mapper via SQLAlchemy ORM.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, case, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """
    Classe Utilisateur conforme au diagramme de classes UML :
    ---------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - nom : String (Nom de famille)
    - prenom : String (Prénom)
    - email : String (Identifiant unique de connexion)
    - motDePasse : String (Empreinte de mot de passe hachée bcrypt)
    - téléphone : String (Numéro de contact téléphonique)

    Héritage vers :
    - Enseignant
    - Responsable

    Association :
    - 1 Utilisateur recevoir 0..* Notification
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    motDePasse = Column("motDePasse", String(255), nullable=False)
    telephone = Column("telephone", String(30), nullable=True)

    # Discriminateur pour l'héritage polymorphique Single Table
    type_user = Column(String(50), nullable=False, default="Utilisateur")

    # Attributs hérités pour le mapping Single Table (Enseignant / Responsable)
    departement = Column(String(100), nullable=True)     # Enum Departement
    gradAcademique = Column(String(100), nullable=True)  # Enum Grade
    specialite = Column(String(100), nullable=True)      # Spécialité métier / académique
    universite = Column(String(50), nullable=True)       # Enum Universite: IIT, ISB

    # Propriétés de compatibilité ascendante avec l'authentification existante
    @property
    def hashed_password(self) -> str:
        return self.motDePasse

    @hashed_password.setter
    def hashed_password(self, val: str):
        self.motDePasse = val

    # --- Sécurité des comptes -------------------------------------------------
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    # Incrémenté à chaque changement de mot de passe / désactivation / déconnexion globale :
    # tous les jetons émis avant (claim "tv") deviennent invalides.
    token_version = Column(Integer, nullable=False, default=0, server_default="0")
    failed_login_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    locked_until = Column(DateTime, nullable=True)
    must_change_password = Column(Boolean, nullable=False, default=False, server_default="false")
    last_login_at = Column(DateTime, nullable=True)

    @hybrid_property
    def role(self) -> str:
        t = (self.type_user or "").strip().lower()
        if t in ("responsable", "administrateur", "admin", "a"):
            return "Administrateur"
        elif t in ("enseignant", "e"):
            return "Enseignant"
        elif t in ("candidat", "c"):
            return "Candidat"
        return "Visiteur"

    @role.expression
    def role(cls):  # utilisable dans les requêtes : User.role == "Enseignant"
        lowered = func.lower(func.trim(cls.type_user))
        return case(
            (lowered.in_(("responsable", "administrateur", "admin", "a")), "Administrateur"),
            (lowered.in_(("enseignant", "e")), "Enseignant"),
            (lowered.in_(("candidat", "c")), "Candidat"),
            else_="Visiteur",
        )

    @role.setter
    def role(self, val: str):
        v = (val or "").strip().lower()
        if v in ("administrateur", "admin", "a", "responsable"):
            self.type_user = "Responsable"
        elif v in ("enseignant", "e"):
            self.type_user = "Enseignant"
        elif v in ("candidat", "c"):
            self.type_user = "Candidat"
        else:
            self.type_user = "Utilisateur"

    # Association : 1 Utilisateur recevoir 0..* Notification
    notifications = relationship("Notification", back_populates="utilisateur", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_on": type_user,
        "polymorphic_identity": "Utilisateur"
    }


class Enseignant(User):
    """
    Classe Enseignant (hérite de Utilisateur) :
    -------------------------------------------
    Attributs spécifiques :
    - departement : Departement (Enum: Civil, Industriel, Informatique, etc.)
    - gradAcadémique : Grade (Enum: MaitreAssistant, Assistant, Professeur, etc.)
    - specialite : String
    - universite : Universite (IIT / ISB)

    Associations (strictement selon le diagramme) :
    - Enseignant organiser 0..* RendezVous (clé étrangère `enseignant_id` sur `rendezvous`)
    NOTE : Pas de liaison directe avec Conversation ou Entretien dans le diagramme.
    """
    __mapper_args__ = {
        "polymorphic_identity": "Enseignant"
    }

    # Relations ORM
    rendezvous_organises = relationship("RendezVous", foreign_keys="RendezVous.enseignant_id", back_populates="enseignant")


class Responsable(User):
    """
    Classe Responsable (hérite de Utilisateur) :
    --------------------------------------------
    Attributs spécifiques :
    - universite : Universite (IIT / ISB)

    Associations (strictement selon le diagramme) :
    - Responsable importer 0..* Document (clé étrangère `responsable_id` sur `documents`)
    NOTE : Pas de liaison directe avec RendezVous dans le diagramme.
    """
    __mapper_args__ = {
        "polymorphic_identity": "Responsable"
    }

    # Relations ORM
    documents = relationship("Document", back_populates="responsable")


class CandidatUser(User):
    """Sous-classe pour l'authentification des comptes candidats (hérite de Utilisateur)."""
    __mapper_args__ = {
        "polymorphic_identity": "Candidat"
    }


# Alias conforme au diagramme de classes UML
Utilisateur = User
