"""Liste noire des jetons JWT révoqués (déconnexion, rotation des refresh tokens)."""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(String(64), primary_key=True)
    # Date d'expiration naturelle du jeton : au-delà, la ligne peut être purgée.
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=False, default=_utcnow)
