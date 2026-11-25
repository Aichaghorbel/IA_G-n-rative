from datetime import timedelta
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import RateLimitExceededException
from app.models.visitor_session import ConversationMessage, VisitorSession, utcnow

LIST_KEYS = {"interets", "matieres_preferees"}
TEXT_KEYS = {"niveau", "objectif_professionnel", "formation_envisagee", "langue"}


class SessionMemoryService:
    @staticmethod
    def add_message(db: Session, session: VisitorSession, role: str, content: str) -> ConversationMessage:
        if role not in ("user", "assistant"):
            raise ValueError("role doit être 'user' ou 'assistant'")
        now = utcnow()

        if role == "user":
            if session.user_message_count >= settings.SESSION_MAX_USER_MESSAGES:
                raise RateLimitExceededException(retry_after=3600, limit=settings.SESSION_MAX_USER_MESSAGES)
            last_minute = (
                db.query(func.count(ConversationMessage.id))
                .filter(ConversationMessage.session_id == session.id,
                        ConversationMessage.role == "user",
                        ConversationMessage.created_at >= now - timedelta(minutes=1))
                .scalar()
            )
            if last_minute >= settings.SESSION_MESSAGES_PER_MINUTE:
                raise RateLimitExceededException(retry_after=60, limit=settings.SESSION_MESSAGES_PER_MINUTE)
            session.user_message_count += 1

        msg = ConversationMessage(
            session_id=session.id,
            role=role,
            content=content[: settings.SESSION_MAX_MESSAGE_CHARS],
            created_at=now,
        )
        db.add(msg)
        db.flush()

        # Limiter le volume : ne garder que les N derniers messages
        cutoff = (
            db.query(ConversationMessage.id)
            .filter(ConversationMessage.session_id == session.id)
            .order_by(ConversationMessage.id.desc())
            .offset(settings.SESSION_MAX_STORED_MESSAGES - 1)
            .limit(1)
            .scalar()
        )
        if cutoff:
            db.query(ConversationMessage).filter(
                ConversationMessage.session_id == session.id,
                ConversationMessage.id < cutoff,
            ).delete(synchronize_session=False)

        # Expiration glissante renouvelée à chaque message
        session.last_seen_at = now
        session.expires_at = now + timedelta(days=settings.VISITOR_SESSION_EXPIRE_DAYS)
        db.commit()
        db.refresh(msg)
        return msg

    @staticmethod
    def get_messages(db: Session, session: VisitorSession, limit: int = None) -> List[ConversationMessage]:
        limit = limit or settings.SESSION_CONTEXT_MESSAGES
        rows = (
            db.query(ConversationMessage)
            .filter(ConversationMessage.session_id == session.id)
            .order_by(ConversationMessage.id.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(rows))  # ordre chronologique

    @staticmethod
    def get_context(db: Session, session: VisitorSession) -> Dict[str, Any]:
        """Contexte à injecter dans le prompt de l'agent IA."""
        return {
            "profile": session.profile or {},
            "messages": [
                {"role": m.role, "content": m.content}
                for m in SessionMemoryService.get_messages(db, session)
            ],
        }

    @staticmethod
    def update_profile(db: Session, session: VisitorSession, facts: Dict[str, Any]) -> Dict[str, Any]:
        profile = dict(session.profile or {})
        for key, value in facts.items():
            if value is None:
                continue
            if key in LIST_KEYS:
                merged = list(profile.get(key, []))
                for item in value:
                    item = str(item).strip()[:100]
                    if item and item not in merged:
                        merged.append(item)
                profile[key] = merged[:20]
            elif key in TEXT_KEYS:
                profile[key] = str(value).strip()[:200]
        session.profile = profile  # nouvel objet : SQLAlchemy détecte le changement JSONB
        db.commit()
        return profile


session_memory_service = SessionMemoryService()