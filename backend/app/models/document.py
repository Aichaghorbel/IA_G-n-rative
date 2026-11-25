"""
Module de modélisation du système documentaire et RAG (Documents, Versions, Traitements).
Strictement conforme au diagramme de classes UML (SmartCampus.drawio / SmartCampus-ClassDiagram.jpg).

Principes appliqués :
- SOLID :
    * SRP : Document (métadonnées du document), VersionDocument (fichier physique et historique), TraitementDocument (journal d'ingestion RAG / OCR / vectorisation).
- Clean Code & Design Patterns :
    * Versioning Pattern pour les documents.
    * Audit Log / Pipeline Processing Pattern via `TraitementDocument`.
"""

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Document(Base):
    """
    Classe Document conforme au diagramme de classes UML :
    ------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - nom : String (Titre du document officiel)
    - description : String
    - categorie : CategorieDoc (Enum: 'Guide', 'Formation')

    Associations :
    - Responsable importer 0..* Document (clé `responsable_id`)
    - 1 Document -> 1..* VersionDocument (composition avec versions)
    - 1 Document effectuer 1..* TraitementDocument (composition avec traitements)
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    categorie = Column(String(50), nullable=False)  # CategorieDoc: Guide, Formation

    responsable_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Relations ORM
    responsable = relationship("Responsable", back_populates="documents")
    versions = relationship("VersionDocument", back_populates="document", cascade="all, delete-orphan")
    traitements = relationship("TraitementDocument", back_populates="document", cascade="all, delete-orphan")

    # Propriétés de compatibilité ascendante
    @property
    def filename(self) -> str:
        return self.nom

    @property
    def type(self) -> str:
        return self.categorie


class VersionDocument(Base):
    """
    Classe VersionDocument conforme au diagramme de classes UML :
    --------------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - nomFichier : String (Nom original du fichier uploadé)
    - cheminFichier : String (Chemin local ou clé S3 MinIO)
    - taille : float (Taille du fichier en Mo / Ko)
    - dateAjout : Date (Date d'ajout de la version)

    Association :
    - 1 Document -> 1..* VersionDocument (clé `document_id`)
    """
    __tablename__ = "version_documents"

    id = Column(Integer, primary_key=True, index=True)
    nomFichier = Column(String(255), nullable=False)
    cheminFichier = Column(String(500), nullable=False)
    taille = Column(Float, nullable=False, default=0.0)
    dateAjout = Column(Date, nullable=True)

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    # Relation ORM
    document = relationship("Document", back_populates="versions")


class TraitementDocument(Base):
    """
    Classe TraitementDocument conforme au diagramme de classes UML :
    -----------------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - type : TraitementType (Enum: 'Ajout', 'Modification', 'Suppression')
    - date : Date (Date du traitement RAG)
    - statut : StautDoc (Enum: 'En cours', 'Terminé', 'Erreur')

    Association :
    - 1 Document effectuer 1..* TraitementDocument (clé `document_id`)
    """
    __tablename__ = "traitement_documents"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)    # TraitementType: Ajout, Modification, Suppression
    date = Column(Date, nullable=True)
    statut = Column(String(50), nullable=False)  # StautDoc: En cours, Terminé, Erreur

    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)

    # Relation ORM
    document = relationship("Document", back_populates="traitements")
