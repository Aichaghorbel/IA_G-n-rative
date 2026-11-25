import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import TokenExpiredException, TokenInvalidException

# Types de jetons : un jeton ne sert QUE pour son usage (anti-confusion de jetons).
TOKEN_ACCESS = "access"
TOKEN_REFRESH = "refresh"
TOKEN_SESSION = "session"
TOKEN_EMAIL_VERIFIED = "email_verified"

# Hash factice : permet de dépenser le même temps de calcul quand l'e-mail n'existe pas
# (évite l'énumération de comptes par mesure du temps de réponse).
_DUMMY_HASH = bcrypt.hashpw(b"smartcampus-dummy", bcrypt.gensalt(rounds=12)).decode("utf-8")


# ==============================================================================
# Mots de passe
# ==============================================================================
def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """Vérifie un mot de passe en clair contre son hash bcrypt (temps constant)."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            (hashed_password or _DUMMY_HASH).encode("utf-8"),
        ) and hashed_password is not None
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Génère le hash bcrypt d'un mot de passe (cost factor 12)."""
    # bcrypt ne traite que 72 octets : on refuse plutôt que de tronquer silencieusement.
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Mot de passe trop long (72 octets max)")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


_PASSWORD_RULES = [
    (re.compile(r".{8,}"), "au moins 8 caractères"),
    (re.compile(r"[A-Z]"), "une majuscule"),
    (re.compile(r"[a-z]"), "une minuscule"),
    (re.compile(r"\d"), "un chiffre"),
]


def password_policy_errors(password: str) -> list[str]:
    """Retourne la liste des règles non respectées (vide si le mot de passe est valide)."""
    missing = [label for rx, label in _PASSWORD_RULES if not rx.search(password)]
    if len(password.encode("utf-8")) > 72:
        missing.append("72 octets maximum")
    return missing


def generate_temporary_password() -> str:
    """Mot de passe temporaire aléatoire cryptographiquement sûr, conforme à la politique."""
    core = secrets.token_urlsafe(9)
    return f"Sc{core}7!"


# ==============================================================================
# Jetons JWT
# ==============================================================================
def _encode(payload: Dict[str, Any]) -> str:
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def _base_claims(token_type: str, expire: datetime, now: datetime) -> Dict[str, Any]:
    return {
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }


def create_access_token(
    subject: Union[str, int],
    role: str,
    email: str,
    token_version: int = 0,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """JWT d'accès (15 min par défaut — spécification section 6.4)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = _base_claims(TOKEN_ACCESS, expire, now)
    payload.update({"sub": str(subject), "role": role, "email": email, "tv": token_version})
    return _encode(payload)


def create_refresh_token(
    subject: Union[str, int],
    token_version: int = 0,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Refresh token (7 jours), à usage unique (rotation + révocation)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    payload = _base_claims(TOKEN_REFRESH, expire, now)
    payload.update({"sub": str(subject), "tv": token_version})
    return _encode(payload)


def create_visitor_session_token(
    session_id: str,
    verified_email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Jeton de session anonyme (visiteur sans compte)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=settings.VISITOR_SESSION_EXPIRE_DAYS))
    payload = _base_claims(TOKEN_SESSION, expire, now)
    payload.update({"session_id": session_id, "role": "Visiteur", "verified_email": verified_email})
    return _encode(payload)


def create_email_verified_token(email: str) -> str:
    """Preuve de possession d'une adresse e-mail (émise après validation de l'OTP)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.VERIFIED_EMAIL_TOKEN_MINUTES)
    payload = _base_claims(TOKEN_EMAIL_VERIFIED, expire, now)
    payload.update({"email": email.lower()})
    return _encode(payload)


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Décode et valide signature, expiration et (optionnellement) le type du jeton.
    Lève TokenExpiredException ou TokenInvalidException.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],  # liste figée : refuse alg=none
            options={"require": ["exp", "iat", "type"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
    except jwt.InvalidTokenError:
        raise TokenInvalidException()

    if expected_type and payload.get("type") != expected_type:
        raise TokenInvalidException("Type de jeton incorrect pour cette opération")
    return payload
