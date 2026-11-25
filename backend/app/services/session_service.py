import hashlib
import hmac
import uuid
from datetime import timedelta
from typing import Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    RateLimitExceededException,
    TokenExpiredException,
    TokenInvalidException,
)
from app.core.security import create_visitor_session_token, decode_token
from app.models.visitor_session import VisitorSession, utcnow


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def hash_ip(ip: str) -> str:
    """HMAC de l'IP avec SECRET_KEY : l'IP n'est jamais stockée en clair."""
    return hmac.new(settings.SECRET_KEY.encode(), ip.encode(), hashlib.sha256).hexdigest()


class SessionService:
    @staticmethod
    def _ttl() -> timedelta:
        return timedelta(days=settings.VISITOR_SESSION_EXPIRE_DAYS)

    @staticmethod
    def purge_expired(db: Session) -> int:
        """Supprime les sessions expirées (les messages partent par ON DELETE CASCADE)."""
        n = db.query(VisitorSession).filter(VisitorSession.expires_at < utcnow()).delete(
            synchronize_session=False
        )
        db.commit()
        return n

    @staticmethod
    def create_session(db: Session, client_ip: Optional[str]) -> Tuple[VisitorSession, str]:
        SessionService.purge_expired(db)
        now = utcnow()

        ip_hash = hash_ip(client_ip) if client_ip else None
        if ip_hash:
            limit = settings.SESSION_CREATE_PER_IP_PER_HOUR
            recent = (
                db.query(func.count(VisitorSession.id))
                .filter(VisitorSession.ip_hash == ip_hash,
                        VisitorSession.created_at >= now - timedelta(hours=1))
                .scalar()
            )
            if recent >= limit:
                raise RateLimitExceededException(retry_after=3600, limit=limit)

        session_id = uuid.uuid4()
        # Le JWT vit longtemps : la vraie expiration (glissante) est expires_at en base.
        token = create_visitor_session_token(str(session_id), expires_delta=timedelta(days=365))

        session = VisitorSession(
            id=session_id,
            token_hash=sha256_hex(token),
            created_at=now,
            last_seen_at=now,
            expires_at=now + SessionService._ttl(),
            profile={},
            ip_hash=ip_hash,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session, token

    @staticmethod
    def authenticate(db: Session, token: str) -> VisitorSession:
        """Valide le token, vérifie l'expiration et prolonge la session (sliding)."""
        payload = decode_token(token)  # TokenInvalid / TokenExpired
        if payload.get("type") != "session":
            raise TokenInvalidException("Ce jeton n'est pas un jeton de session visiteur")
        try:
            session_id = uuid.UUID(str(payload.get("session_id")))
        except ValueError:
            raise TokenInvalidException("Session visiteur invalide")

        session = db.get(VisitorSession, session_id)
        if not session or not hmac.compare_digest(session.token_hash, sha256_hex(token)):
            raise TokenInvalidException("Session visiteur introuvable")

        now = utcnow()
        if session.expires_at <= now:
            raise TokenExpiredException("Session visiteur expirée")

        session.last_seen_at = now
        session.expires_at = now + SessionService._ttl()
        db.commit()
        return session

    @staticmethod
    def delete_session(db: Session, session: VisitorSession) -> None:
        db.delete(session)  # supprime aussi les messages (RGPD)
        db.commit()


session_service = SessionService()