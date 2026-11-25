
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger, CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow() -> datetime:
    """UTC naïf, cohérent avec les colonnes TIMESTAMP."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class VisitorSession(Base):
    __tablename__ = "visitor_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    last_seen_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    profile = Column(JSONB, nullable=False, default=dict, server_default="{}")
    candidate_id = Column(Integer, ForeignKey("candidats.id", ondelete="SET NULL"), nullable=True)
    ip_hash = Column(String(64), nullable=True, index=True)
    user_message_count = Column(Integer, nullable=False, default=0, server_default="0")

    messages = relationship(
        "ConversationMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ConversationMessage.id",
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_conv_messages_role"),
        Index("ix_conv_messages_session_id_id", "session_id", "id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("visitor_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(16), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    session = relationship("VisitorSession", back_populates="messages")