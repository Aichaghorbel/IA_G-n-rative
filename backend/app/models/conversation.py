"""
Module de modélisation du système conversationnel (Conversations, Messages, Réponses Générées par l'IA).
Strictement conforme au diagramme de classes UML (SmartCampus.drawio / SmartCampus-ClassDiagram.jpg).

Principes appliqués :
- SOLID :
    * SRP : Conversation (historique/contexte de chat), Message (message utilisateur), Reponse (réponse générée par l'agent IA).
- Clean Code & Design Patterns :
    * 1-to-1 Association (Message -> Reponse / ReponseGeneree).
    * Conversation liée soit à un Visiteur, soit à un Candidat (aucune liaison directe avec Enseignant).
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Conversation(Base):
    """
    Classe Conversation conforme au diagramme de classes UML :
    ----------------------------------------------------------
    Attributs :
    - idConversation : int (Clé primaire)
    - titre : String (Titre contextuel du fil de discussion)
    - estFavori : bool (Marquage en favori)
    - dateDernierModification : Date / DateTime (Dernière activité)

    Associations (strictement selon le diagramme) :
    - Visiteur démarrer 0..* Conversation (clé `visiteur_id`)
    - Candidat démarrer 0..* Conversation (clé `candidat_id`)
    - 1 Conversation -> 1..* Message
    NOTE : Aucune liaison directe avec Enseignant dans le diagramme.
    """
    __tablename__ = "conversations"

    idConversation = Column(Integer, primary_key=True, index=True)
    titre = Column(String(200), nullable=True)
    estFavori = Column(Boolean, default=False)
    dateDernierModification = Column(DateTime, nullable=True)

    # FK : Visiteur démarrer Conversation
    visiteur_id = Column(Integer, ForeignKey("visiteurs.id"), nullable=True, index=True)
    # FK : Candidat démarrer Conversation
    candidat_id = Column(Integer, ForeignKey("candidats.id"), nullable=True, index=True)
    # NOTE : enseignant_id supprimé — absent du diagramme de classes

    # Relations ORM
    visiteur = relationship("Visiteur", back_populates="conversations")
    candidat = relationship("Candidat", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

    # Propriété de compatibilité ascendante
    @property
    def id(self) -> int:
        return self.idConversation


class Message(Base):
    """
    Classe Message conforme au diagramme de classes UML :
    -----------------------------------------------------
    Attributs :
    - idMessage : int (Clé primaire)
    - contenu : String (Corps du message textuel)
    - dateEnvoi : Date / DateTime (Date et heure d'émission)

    Associations :
    - 1 Conversation -> 1..* Message (clé `conversation_id`)
    - 1 Message -> 1 Reponse (ReponseGeneree)
    """
    __tablename__ = "messages"

    idMessage = Column(Integer, primary_key=True, index=True)
    contenu = Column(String(2000), nullable=False)
    dateEnvoi = Column(DateTime, nullable=True)

    conversation_id = Column(Integer, ForeignKey("conversations.idConversation"), nullable=False, index=True)

    # Relations ORM
    conversation = relationship("Conversation", back_populates="messages")
    reponse = relationship("Reponse", uselist=False, back_populates="message", cascade="all, delete-orphan")

    # Propriétés de compatibilité ascendante
    @property
    def id(self) -> int:
        return self.idMessage

    @property
    def content(self) -> str:
        return self.contenu

    @property
    def role(self) -> str:
        return "user"


class Reponse(Base):
    """
    Classe ReponseGeneree / Reponse conforme au diagramme de classes UML :
    ----------------------------------------------------------------------
    Attributs :
    - id : int (Clé primaire)
    - contenu : String (Réponse synthétisée par l'agent IA)
    - date : Date / DateTime
    - source : String (Source documentaire ou URL RAG)

    Association :
    - 1 Message -> 1 Reponse : Clé étrangère 1-to-1 `message_id`
    """
    __tablename__ = "reponses"

    id = Column(Integer, primary_key=True, index=True)
    contenu = Column(String(2000), nullable=False)
    date = Column(DateTime, nullable=True)
    source = Column(String(500), nullable=True)

    message_id = Column(Integer, ForeignKey("messages.idMessage"), unique=True, nullable=False, index=True)

    # Relation ORM
    message = relationship("Message", back_populates="reponse")


# Alias conforme au diagramme de classes UML
ReponseGeneree = Reponse
