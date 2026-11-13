from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)  # uuid v4 session visiteur
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=True, index=True)
    is_anonymous = Column(Boolean, default=True)
    language_detected = Column(String(20), default="fr")         # fr, tn, arabizi
    intent_detected = Column(String(50), default="info_programme") # info_programme, orientation, preinscription, qcm, rdv, autre
    memory_summary = Column(JSON, default=dict)                 # {interets: [], niveau: "", formations_envisagees: []}
    audio_enabled = Column(Boolean, default=False)              # Préférence audio
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)                  # user, assistant, system
    content = Column(Text, nullable=False)
    audio_url = Column(String(500), nullable=True)
    language_detected = Column(String(20), default="fr")
    sources = Column(JSON, default=list)                       # [{"document_id": 12, "title": "...", "page": 3}]
    metadata_json = Column(JSON, default=dict)                 # {intent, score, latency_ms, tokens_used, model}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="messages")
